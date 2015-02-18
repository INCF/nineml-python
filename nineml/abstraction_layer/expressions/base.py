"""
This file defines mathematical classes and derived classes

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from copy import deepcopy
import sympy.printing
import re

# import math_namespace
from nineml.exceptions import NineMLRuntimeError
from .utils import MathUtil, is_valid_lhs_target
from .. import BaseALObject


class Expression(object):

    """ This is a base class for Expressions and Conditionals which provides
    the basic interface for parsing, yielding of python functions,
    C equivalents, name substitution """

    defining_attributes = ('_rhs',)

    _func_re = re.compile(r'(\w+)\(')

    def __init__(self, rhs):
        self.rhs = rhs

    def __eq__(self, other):
        return self._rhs == other._rhs

    @property
    def rhs(self):
        return self._rhs

    @rhs.setter
    def rhs(self, rhs):
        try:
            self._rhs = sympy.sympify(rhs)
        except sympy.SympifyError:
            raise NineMLRuntimeError(
                "Could not parse math-inline expression: {}"
                .format(rhs))

    @property
    def rhs_symbols(self):
        return self._rhs.free_symbols

    @property
    def rhs_symbol_names(self):
        return (str(s) for s in self.rhs_symbols)

    @property
    def rhs_funcs(self):
        return self._func_re.findall(str(self._rhs))

    @property
    def rhs_atoms(self):
        """Returns an iterator over all the variable names and mathematical
        functions on the RHS function. This does not include defined
        mathematical symbols such as ``pi`` and ``e``, but does include
        functions such as ``sin`` and ``log`` """

        return chain(self.rhs_symbol_names, self.rhs_funcs)

    def rhs_suffix(self, suffix, prefix='', excludes=[]):
        expr = deepcopy(self._rhs)
        for symbol in self.rhs_symbol_names:
            if symbol not in excludes:
                expr = expr.subs(symbol, prefix + symbol + suffix)
        return expr

    def rhs_as_python_func(self):
        """ Returns a python callable which evaluates the expression in
        namespace and returns the result """
        return eval('lambda {}: {}'
                    .format(', '.join(self.rhs_symbol_names),
                            sympy.printing.python(self.rhs)[4:]))

    def rhs_name_transform_inplace(self, name_map):
        """Replace atoms on the RHS with values in the name_map"""
        self._rhs = self.rhs_substituted(name_map)

    def rhs_substituted(self, name_map):
        expr = self.rhs
        for old, new in name_map.iteritems():
            expr = self.rhs.subs(old, new)
        return expr

    def rhs_str_with_renamed_functions(self, name_map):
        expr_str = str(self.rhs)
        for old, new in name_map:
            expr_str = re.sub(r'(?<!\w)({})\('.format(old), new, expr_str)
        return expr_str


class ExpressionWithLHS(Expression):
    # Sub-classes should override this, to allow
    # proper-prefixing:

    def __init__(self, rhs):
        Expression.__init__(self, rhs)

    def name_transform_inplace(self, name_map):

        # Transform the lhs & rhs:
        self.lhs_name_transform_inplace(name_map)
        self.rhs_name_transform_inplace(name_map)

    @property
    def atoms(self):
        """Returns a list of the atoms in the LHS and RHS of this expression"""
        return chain(self.rhs_atoms, self.lhs_atoms)

    def lhs_name_transform_inplace(self, name_map):
        raise NotImplementedError()

    @property
    def lhs_atoms(self):
        raise NotImplementedError()

    def __eq__(self, other):
        return (super(ExpressionWithLHS, self).__eq__(other) and
                self.lhs == other.lhs)


class ExpressionWithSimpleLHS(ExpressionWithLHS):

    """Represents a an equation with a simple left-hand-side.
    That is, a single symbol, for example 's = t+1'
    """

    defining_attributes = ('_lhs', '_rhs')

    def __init__(self, lhs, rhs):
        ExpressionWithLHS.__init__(self, rhs)

        if not MathUtil.is_single_symbol(lhs):
            err = 'Expecting a single symbol on the LHS; got: %s' % lhs
            raise NineMLRuntimeError(err)
        if not is_valid_lhs_target(lhs):
            err = 'Invalid LHS target: %s' % lhs
            raise NineMLRuntimeError(err)

        self._lhs = lhs.strip()

    @property
    def lhs(self):
        return self._lhs

    @property
    def lhs_atoms(self):
        return [self.lhs]

    def lhs_name_transform_inplace(self, name_map):
        self._lhs = name_map.get(self.lhs, self.lhs)


class ODE(ExpressionWithLHS):

    """ An ordinary, first order differential equation.

        .. note::

            These should not be created directly, this class is
            used as base class for ``TimeDerivative``

    """

    def __init__(self, dependent_variable, independent_variable, rhs):
        ExpressionWithLHS.__init__(self, rhs)

        self._dependent_variable = dependent_variable
        self._independent_variable = independent_variable

    def __repr__(self):
        return "ODE(d%s/d%s = %s)" % (self.dependent_variable,
                                      self.independent_variable,
                                      self.rhs)

    @property
    def lhs(self):
        """Return a string of the lhs of the form: 'dS/dt' """
        return "d%s/d%s" % (self.dependent_variable, self.independent_variable)

    @property
    def dependent_variable(self):
        """Return the dependent variable"""
        return self._dependent_variable

    @property
    def independent_variable(self):
        """Return the independent variable"""
        return self._independent_variable

    def lhs_name_transform_inplace(self, name_map):
        """Replace atoms on the LHS with mapping in name_map """

        dep = self._dependent_variable
        self._dependent_variable = name_map.get(dep, dep)

        indep = self._independent_variable
        self._independent_variable = name_map.get(indep, indep)

    @property
    def lhs_atoms(self):
        return [self.independent_variable, self.dependent_variable]


class Alias(BaseALObject, ExpressionWithSimpleLHS):

    """Aliases are a way of defining a variable local to a ``ComponentClass``,
    in terms of its ``Parameters``, ``StateVariables`` and input ``Analog
    Ports``. ``Alias``es allow us to reduce the duplication of code in
    ComponentClass definition, and allow allow more complex outputs to
    ``AnalogPort`` than simply individual ``StateVariables``.

   When specified from a ``string``, an alias uses the notation ``:=``

    ``Alias``es can be defined in terms of other ``Alias``es, so for example,
    if we had ComponentClass representing a Hodgkin-Huxley style gating
    channel, which has a ``Property``, `reversal_potential`, and an input
    ``AnalogPort``, `membrane_voltage`, then we could define an ``Alias``::

        ``driving_force := reversal_potential - membrane_voltage``

    If the relevant ``StateVariables``, ``m`` and ``h``, for example were also
    defined, and a ``Parameter``, ``g_bar``, we could also define the current
    flowing through this channel as::

        current := driving_force * g * m * m * m * h

    This current could then be attached to an output ``AnalogPort`` for
    example.

    It is important to ensure that Alias definitions are not circular, for
    example, it is not valid to define two alias in terms of each other::

        a := b + 1
        b := 2 * a

    During code generation, we typically call ``ComponentClass.backsub_all()``.
    This method first expands each alias in terms of other aliases, such that
    each alias depends only on Parameters, StateVariables and *incoming*
    AnalogPort. Next, it expands any alias definitions within TimeDerivatives,
    StateAssignments, Conditions and output AnalogPorts.



    """
    element_name = 'Alias'
    defining_attributes = ('_lhs', '_rhs')

    def __init__(self, lhs=None, rhs=None):
        """ Constructor for an Alias

        :param lhs: A `string` specifying the left-hand-side, i.e. the Alias
            name. This should be a single `symbol`.
        :param rhs: A `string` specifying the right-hand-side. This should be a
            mathematical expression, expressed in terms of other Aliases,
            StateVariables, Parameters and *incoming* AnalogPorts local to the
            Component.

        """
        ExpressionWithSimpleLHS.__init__(self, lhs, rhs)

    def __repr__(self):
        return "<Alias: %s := %s>" % (self.lhs, self.rhs)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_alias(self, **kwargs)

    @classmethod
    def from_str(cls, alias_string):
        """Creates an Alias object from a string"""
        if not cls.is_alias_str(alias_string):
            errmsg = "Invalid Alias: %s" % alias_string
            raise NineMLRuntimeError(errmsg)

        lhs, rhs = alias_string.split(':=')
        return Alias(lhs=lhs.strip(), rhs=rhs.strip())

    @classmethod
    def is_alias_str(cls, alias_str):
        """ Returns True if the string could be an alias"""
        return ':=' in alias_str


class Constant(BaseALObject):

    element_name = 'Constant'
    defining_attributes = ('name', 'value', 'units')

    def __init__(self, name, value, units):
        self.name = name
        self.value = value
        self.units = units

    def __repr__(self):
        return ("Constant(name={}, value={}, units={})"
                .format(self.name, self.value, self.units))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_constant(self, **kwargs)

    def name_transform_inplace(self, name_map):
        try:
            self.name = name_map[self.name]
        except KeyError:
            assert False, "'{}' was not found in name_map".format(self.name)

    def set_units(self, units):
        assert self.units == units, \
            "Renaming units with ones that do not match"
        self.units = units
