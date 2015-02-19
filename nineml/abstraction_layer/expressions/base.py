"""
This file defines mathematical classes and derived classes

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from __future__ import division
from itertools import chain, izip
from copy import deepcopy
import sympy
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, convert_xor)
from sympy.parsing.sympy_tokenize import NAME, OP
from sympy.printing import print_ccode
import re


# import math_namespace
from nineml.exceptions import NineMLRuntimeError, NineMLMathParseError
from .. import BaseALObject

builtin_constants = set(['pi', 'true', 'false', 'True', 'False'])
builtin_functions = set([
    'exp', 'sin', 'cos', 'log', 'log10', 'pow', 'abs',
    'sinh', 'cosh', 'tanh', 'sqrt', 'mod', 'sum',
    'atan', 'asin', 'acos', 'asinh', 'acosh', 'atanh', 'atan2'])
reserved_symbols = set(['t'])


class Expression(object):

    """ This is a base class for Expressions and Conditionals which provides
    the basic interface for parsing, yielding of python functions,
    C equivalents, name substitution """

    defining_attributes = ('_rhs',)

    # Regular expression for extracting function names from strings (i.e. a
    # chain of valid identifiers follwed by an open parenthesis.
    _func_re = re.compile(r'(\w+) *\(')  # Match identifier followed by (
    _escape_random_re = re.compile(r'(?<!\w)random\.(\w+) *\(')
    _unescape_random_re = re.compile(r'(?<!\w)random_(\w+)_\(')
    _strip_parens_re = re.compile(r'^\(+(\w+)\)+$')  # Match if enclosed by ()

    # Inline randoms are deprecated in favour of RandomVariable elements,
    # but included here to get Brunel model to work
    _builtin_randoms = {
        'random_uniform_': sympy.Function('random_uniform_'),
        'random_binomial_': sympy.Function('random_binomial_'),
        'random_poisson_': sympy.Function('random_poisson_'),
        'random_exponential_': sympy.Function('random_exponential_')}

    class SympyEscaper(object):
        # Escape all objects in sympy namespace that aren't defined in NineML
        # by predefining them as symbol names to avoid naming conflicts when
        # sympifying RHS strings.
        _to_escape = set(s for s in dir(sympy)
                         if s not in chain(builtin_constants,
                                           builtin_functions))

        def __init__(self):
            self.escaped_names = set()

        def __call__(self, tokens, local_dict, global_dict):  # @UnusedVariable
            """
            Escapes symbols that correspond to objects in SymPy but are not
            reserved identifiers in NineML
            """
            result = []
            for toknum, tokval in tokens:
                if toknum == NAME and tokval in self._to_escape:
                    self.escaped_names.add(tokval)
                    tokval = self.escape(tokval)
                elif toknum == OP and tokval.startswith('!'):
                    # NB: Multiple !'s are grouped into the one token
                    assert all(t == '!' for t in tokval)
                    if len(tokval) % 2:
                        tokval = '~'
                    else:
                        continue
                elif toknum == NAME and tokval == 'true':
                    tokval = 'True'
                elif toknum == NAME and tokval == 'false':
                    tokval = 'False'
                result.append((toknum, tokval))
            # Handle trivial corner cases where the logical identities (i.e.
            # True and False) are immediately negated (damn unit-tests making
            # things more complicated than the need to be!;), as Sympy casts
            # True and False to the Python native objects, and then the '~'
            # gets interpreted as a bitwise shift rather than a negation.
            # Solution: drop the negation sign and negate manually.
            new_result = []
            pair_iterator = izip(result[:-1], result[1:])
            for (toknum, tokval), (next_toknum, next_tokval) in pair_iterator:
                if ((toknum == OP and tokval == '~') and
                    (next_toknum == NAME and
                     next_tokval in ('True', 'False'))):
                    tokval = 'True' if next_tokval is 'False' else 'False'
                    toknum = NAME
                    next(pair_iterator)  # Skip the next iteration
                new_result.append((toknum, tokval))
            return new_result

        @classmethod
        def escape(self, s):
            return s + '_'

    def __repr__(self):
        return "{}(rhs='{}')".format(self.__class__.__name__, self.rhs_str)

    @classmethod
    def reserved_identifiers(cls):
        return chain(builtin_constants, builtin_functions,
                     reserved_symbols, cls._builtin_randoms.iterkeys())

    def __init__(self, rhs):
        self.rhs = rhs

    def __eq__(self, other):
        return sympy.simplify(self.rhs - other.rhs) == 0

    @property
    def rhs(self):
        return self._rhs

    @rhs.setter
    def rhs(self, rhs):
        if isinstance(rhs, sympy.Basic):
            fnames = self._func_re.findall(str(rhs))
            assert (not fnames or
                    all(fnames in chain(builtin_functions,
                                        ('And', 'Or', 'Not')))), \
                    ("Invalid functions found in Sympy expression: {}"
                     .format(rhs))
            self._rhs = rhs
        else:
            try:
                # Inline randoms are deprecated but included to get Brunel
                # model to work
                rhs = str(rhs)
                rhs = self._escape_random_re.sub(r'random_\1_(', rhs)
                sympy_escaper = self.SympyEscaper()
                transformations = ([sympy_escaper, convert_xor] +
                                   list(standard_transformations))
                self._rhs = parse_expr(rhs, transformations=transformations,
                                       local_dict=self._builtin_randoms)
                for n in sympy_escaper.escaped_names:
                    self._rhs = self._rhs.xreplace(
                        {sympy.Symbol(sympy_escaper.escape(n)):
                            sympy.Symbol(n)})
            except Exception, e:
                raise NineMLMathParseError(
                    "Could not parse math-inline expression: {}\n\n{}"
                    .format(rhs, e))

    @property
    def rhs_str(self):
        try:
            if self._rhs.is_Boolean:
                expr_str = self._unwrap_bool(self.rhs)
            else:
                expr_str = str(self._rhs)
        except AttributeError:  # For expressions that have simplified
            expr_str = str(self._rhs)
        expr_str = str(expr_str).replace('**', '^')
        expr_str = self._unescape_random_re.sub(r'random_\1_(', expr_str)
        return expr_str

    @classmethod
    def _unwrap_bool(cls, expr):
        """
        Recursive helper method to unwrap boolean expressions
        """
        if isinstance(expr, sympy.And):
            arg1 = cls._unwrap_bool(expr.args[0])
            arg2 = cls._unwrap_bool(expr.args[1])
            expr_str = '({}) & ({})'.format(arg1, arg2)
        elif isinstance(expr, sympy.Or):
            arg1 = cls._unwrap_bool(expr.args[0])
            arg2 = cls._unwrap_bool(expr.args[1])
            expr_str = '({}) | ({})'.format(arg1, arg2)
        elif isinstance(expr, sympy.Not):
            expr_str = '!({})'.format(arg1, arg2)
        else:
            expr_str = str(expr)
        return expr_str

    @property
    def rhs_symbols(self):
        try:
            return self._rhs.free_symbols
        except AttributeError:  # For expressions that have been simplified
            return []

    @property
    def rhs_symbol_names(self):
        return (self._strip_parens_re.sub(r'\1', str(s))
                for s in self.rhs_symbols)

    @property
    def rhs_funcs(self):
        return (f for f in self._func_re.findall(self.rhs_str)
                if f not in self._builtin_randoms.itervalues())

    @property
    def rhs_atoms(self):
        """Returns an iterator over all the variable names and mathematical
        functions on the RHS function. This does not include defined
        mathematical symbols such as ``pi`` and ``e``, but does include
        functions such as ``sin`` and ``log`` """

        return (str(a) for a in chain(self.rhs_symbol_names, self.rhs_funcs))

    @property
    def rhs_cstr(self):
        return print_ccode(self._rhs)

    @property
    def rhs_as_python_func(self):
        """ Returns a python callable which evaluates the expression in
        namespace and returns the result """
        def nineml_expression(**kwargs):
            if isinstance(self.rhs, (bool, int, float)):
                val = self.rhs
            else:
                if self.rhs.is_Boolean:
                    try:
                        val = self.rhs.subs(kwargs)
                    except Exception:
                        raise NineMLRuntimeError(
                            "Incorrect arguments provided to expression ('{}')"
                            ": '{}'\n".format(
                                "', '".join(self.rhs_symbol_names),
                                "', '".join(kwargs.keys())))
                else:
                    try:
                        val = self.rhs.evalf(subs=kwargs)
                    except Exception:
                        raise NineMLRuntimeError(
                            "Incorrect arguments provided to expression ('{}')"
                            ": '{}'\n".format(
                                "', '".join(self.rhs_symbol_names),
                                "', '".join(kwargs.keys())))
                    try:
                        val = float(val)
                    except TypeError:
                        try:
                            locals_dict = deepcopy(kwargs)
                            locals_dict.update(str_to_npfunc_map)
                            val = eval(str(val), {}, locals_dict)
                        except Exception:
                            raise NineMLRuntimeError(
                                "Could not evaluate expression: {}"
                                .format(self.rhs_str))
            return val
        return nineml_expression

    def rhs_suffixed(self, suffix='', prefix='', excludes=[]):
        return self.rhs.xreplace(dict(
            (s, sympy.Symbol(prefix + str(s) + suffix))
            for s in self.rhs_symbols if str(s) not in excludes))

    def rhs_name_transform_inplace(self, name_map):
        """Replace atoms on the RHS with values in the name_map"""
        self._rhs = self.rhs_substituted(name_map)

    def rhs_substituted(self, name_map):
        return self.rhs.xreplace(dict((sympy.Symbol(old), sympy.Symbol(new))
                                      for old, new in name_map.iteritems()))

    def rhs_str_substituted(self, name_map={}, funcname_map={}):
        expr_str = str(self.rhs_substituted(name_map))
        for old, new in funcname_map:
            expr_str = re.sub(r'(?<!\w)({})\('.format(old), new, expr_str)
        expr_str = expr_str.replace('**', '^')
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

        if not is_single_symbol(lhs):
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

from .utils import str_to_npfunc_map, is_single_symbol, is_valid_lhs_target
