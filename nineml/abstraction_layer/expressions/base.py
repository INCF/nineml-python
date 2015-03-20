"""
This file defines mathematical classes and derived classes

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from __future__ import division
from itertools import chain
from copy import deepcopy
import sympy
from sympy.printing import ccode
import re
# import math_namespace
from nineml.exceptions import NineMLRuntimeError

builtin_constants = set(['pi', 'true', 'false', 'True', 'False'])
builtin_functions = set([
    'exp', 'sin', 'cos', 'log', 'log10', 'pow', 'abs',
    'sinh', 'cosh', 'tanh', 'sqrt', 'mod', 'sum',
    'atan', 'asin', 'acos', 'asinh', 'acosh', 'atanh', 'atan2'])
reserved_symbols = set(['t'])
reserved_identifiers = set(chain(builtin_constants, builtin_functions,
                                 reserved_symbols))
from .parser import Parser


class Expression(object):

    """ This is a base class for Expressions and Conditionals which provides
    the basic interface for parsing, yielding of python functions,
    C equivalents, name substitution """

    defining_attributes = ('rhs',)

    # Regular expression for extracting function names from strings (i.e. a
    # chain of valid identifiers follwed by an open parenthesis.
    _func_re = re.compile(r'([\w\.]+) *\(')  # Match identifier followed by (
    _strip_parens_re = re.compile(r'^\(+(\w+)\)+$')  # Match if enclosed by ()

    def __init__(self, rhs):
        self.rhs = rhs

    def __eq__(self, other):
        return sympy.simplify(self.rhs - other.rhs) == 0

    @property
    def rhs(self):
        return self._rhs

    @rhs.setter
    def rhs(self, rhs):
        self._rhs = Parser().parse(rhs)  # Maybe this parser could be reused??

    def __str__(self):
        return self.rhs_str

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.rhs_str)

    @property
    def rhs_str(self):
        try:
            if self._rhs.is_Boolean:
                expr_str = self._unwrap_bool(self.rhs)
            else:
                expr_str = str(self._rhs)
        except AttributeError:
            # For expressions that have simplified to Python objects (e.g.
            # True, False,...)
            expr_str = str(self._rhs)
        expr_str = Parser.unescape_random_namespace(expr_str)
        expr_str = expr_str.replace('**', '^')
        return expr_str

    @classmethod
    def _unwrap_bool(cls, expr):
        """
        Recursive helper method to unwrap boolean expressions
        """
        if isinstance(expr, sympy.And):
            arg1 = cls._unwrap_bool(expr.args[0])
            arg2 = cls._unwrap_bool(expr.args[1])
            expr_str = '({}) && ({})'.format(arg1, arg2)
        elif isinstance(expr, sympy.Or):
            arg1 = cls._unwrap_bool(expr.args[0])
            arg2 = cls._unwrap_bool(expr.args[1])
            expr_str = '({}) || ({})'.format(arg1, arg2)
        elif isinstance(expr, sympy.Not):
            expr_str = '!({})'.format(arg1, arg2)
        else:
            expr_str = str(expr)
        return expr_str

    @property
    def rhs_cstr(self):
        rhs = self._unwrap_integer_powers(self._rhs)
        cstr = ccode(rhs)
        cstr = Parser.unescape_random_namespace(cstr)
        return cstr

    @property
    def rhs_symbols(self):
        try:
            return self._rhs.free_symbols
        except AttributeError:  # For expressions that have been simplified
            return []

    @property
    def rhs_symbol_names(self):
        # FIXME: Might be a better way to ensure there are no parentheses
        return (self._strip_parens_re.sub(r'\1', str(s))
                for s in self.rhs_symbols)

    @property
    def rhs_funcs(self):
        try:
            return (type(f) for f in self._rhs.atoms(sympy.Function)
                    if type(f) not in Parser.inline_random_distributions())
        except AttributeError:  # For expressions that have been simplified
            return []

    @property
    def rhs_atoms(self):
        """Returns an iterator over all the variable names and mathematical
        functions on the RHS function. This does not include defined
        mathematical symbols such as ``pi`` and ``e``, but does include
        functions such as ``sin`` and ``log`` """
        return (str(a) for a in chain(self.rhs_symbol_names, self.rhs_funcs))

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
        """
        Return copy of expression with all free symols suffixed (or prefixed)
        """
        return self.rhs.xreplace(dict(
            (s, sympy.Symbol(prefix + str(s) + suffix))
            for s in self.rhs_symbols if str(s) not in excludes))

    def rhs_name_transform_inplace(self, name_map):
        """Replace atoms on the RHS with values in the name_map in place"""
        self._rhs = self.rhs_substituted(name_map)

    def rhs_substituted(self, name_map):
        """Replace atoms on the RHS with values in the name_map"""
        return self.rhs.xreplace(dict((sympy.Symbol(old), sympy.Symbol(new))
                                      for old, new in name_map.iteritems()))

    def rhs_str_substituted(self, name_map={}, funcname_map={}):
        """
        Replaces names and function names. Deprecated
        """
        expr_str = str(self.rhs_substituted(name_map))
        for old, new in funcname_map:
            expr_str = re.sub(r'(?<!\w)({})\('.format(old), new, expr_str)
        expr_str = expr_str.replace('**', '^')
        return expr_str

    def __iadd__(self, expr):
        "self += expr"
        self.rhs = self.rhs + expr
        return self

    def __isub__(self, expr):
        "self -= expr"
        self.rhs = self.rhs - expr
        return self

    def __imul__(self, expr):
        "self *= expr"
        self.rhs = self.rhs * expr
        return self

    def __itruediv__(self, expr):
        "self /= expr"
        self.rhs = self.rhs / expr
        return self

    def __ipow__(self, expr):
        "self **= expr"
        self.rhs = self.rhs ** expr
        return self

    def __iand__(self, expr):
        "self &= expr"
        self.rhs = sympy.And(self.rhs, expr)
        return self

    def __ior__(self, expr):
        "self |= expr"
        self.rhs = sympy.Or(self.rhs, expr)
        return self

    def negate(self):
        self.rhs = sympy.Not(self.rhs)
        return self

    def simplify(self):
        self.rhs = sympy.simplify(self.rhs)

    @classmethod
    def _unwrap_integer_powers(cls, expr):
        """
        Convert integer powers in an expression to Muls, like a**2 => a*a.
        """
        integer_pows = list(p for p in expr.atoms(sympy.Pow)
                            if p.as_base_exp()[1].is_Integer)
        repl = zip(integer_pows,
                   (sympy.Mul(*[b] * e, evaluate=False)
                    for b, e in (i.as_base_exp() for i in integer_pows)))
        return cls._non_eval_xreplace(expr, dict(repl))

    @classmethod
    def _non_eval_xreplace(cls, expr, rule):
        """
        Duplicate of sympy's xreplace but with non-evaluate statement included
        """
        if expr in rule:
            return rule[expr]
        elif rule:
            args = []
            altered = False
            for a in expr.args:
                try:
                    new_a = cls._non_eval_xreplace(a, rule)
                except AttributeError:
                    new_a = a
                if new_a != a:
                    altered = True
                args.append(new_a)
            args = tuple(args)
            if altered:
                return expr.func(*args, evaluate=False)
        return expr


class ExpressionSymbol(object):
    """
    Base class for all NineML objects that can be treated like Sympy symbols
    """

    def _sympy_(self):
        return sympy.Symbol(self.name)

    def __add__(self, other):
        return sympy.sympify(self) + other

    def __sub__(self, other):
        return sympy.sympify(self) - other

    def __mul__(self, other):
        return sympy.sympify(self) * other

    def __truediv__(self, other):
        return sympy.sympify(self) / other

    def __mod__(self, other):
        return sympy.sympify(self) % other

    def __pow__(self, other):
        return sympy.sympify(self) ** other

    def __and__(self, other):
        return sympy.sympify(self) & other

    def __or__(self, other):
        return sympy.sympify(self) | other


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


class ExpressionWithSimpleLHS(ExpressionWithLHS, ExpressionSymbol):

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

    def __str__(self):
        return '{} := {}'.format(self.lhs, self.rhs_str)

    def __repr__(self):
        return "{}(lhs='{}', rhs=({}))".format(self.__class__.__name__,
                                               self.lhs, self.rhs_str)

    @property
    def lhs(self):
        return self._lhs

    @property
    def lhs_atoms(self):
        return [self.lhs]

    def lhs_name_transform_inplace(self, name_map):
        self._lhs = name_map.get(self.lhs, self.lhs)

    def _sympy_(self):
        return sympy.Symbol(self.lhs)


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

from .utils import str_to_npfunc_map, is_single_symbol, is_valid_lhs_target
