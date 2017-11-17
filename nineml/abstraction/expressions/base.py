"""
This file defines mathematical classes and derived classes

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from __future__ import division
from builtins import object
from past.builtins import basestring
from itertools import chain
from copy import deepcopy
import sympy
from sympy.printing import ccode
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
from sympy.functions.elementary.piecewise import ExprCondPair
import re
from nineml.utils import validate_identifier
# import math_namespace
from nineml.base import AnnotatedNineMLObject
from nineml.exceptions import NineMLUsageError


builtin_constants = set(['true', 'false', 'True', 'False'])
builtin_functions = set([
    'exp', 'sin', 'cos', 'log', 'log10', 'pow', 'abs',
    'sinh', 'cosh', 'tanh', 'sqrt', 'mod',  # 'sum',
    'atan', 'asin', 'acos', 'asinh', 'acosh', 'atanh', 'atan2'])
reserved_symbols = set(['t'])
reserved_identifiers = set(chain(builtin_constants, builtin_functions,
                                 reserved_symbols))
from .parser import Parser  # @IgnorePep8


t = sympy.Symbol('t')  # The symbol for time


class Expression(AnnotatedNineMLObject):

    """
    Base class for Expressions and Conditionals which provides
    the basic interface for parsing, yielding of python functions,
    C equivalents, name substitution

    Parameters
    ----------
    rhs : str | Sympy.Basic
        The expression in string or Sympy_ form
    """

    nineml_type = '_Expression'
    nineml_attr = ('rhs',)

    # Regular expression for extracting function names from strings (i.e. a
    # chain of valid identifiers followed by an open parenthesis.
    _func_re = re.compile(r'([\w\.]+) *\(')  # Match identifier followed by (
    _strip_parens_re = re.compile(r'^\(+(\w+)\)+$')  # Match if enclosed by ()
    _random_map = dict((str(v), Parser.unescape_random_namespace(k))
                       for k, v in Parser.inline_randoms_dict.items())
    # The inline randoms are not actually unescaped back to their "random.*"
    # format, and are instead retained in their escaped format "random_*_",
    # but this needs to be included into the cfunc_map to avoid
    # "//Not Supported in C being prepended to the c string
    _cfunc_map = dict([(str(v), str(v))
                       for k, v in Parser.inline_randoms_dict.items()] +
                      [('abs', 'fabs')])
    _rationals_re = re.compile(r'(?<!\w)([\d\.]+)L/(?<!\w)([\d\.]+)L')
    _multiple_whitespace_re = re.compile(r'\s+')
    _ccode_print_warn_re = re.compile(r'// (?:Not supported in C:|abs)\n')

    def __init__(self, rhs, **kwargs):
        super(Expression, self).__init__(**kwargs)
        self.rhs = rhs

    @property
    def rhs(self):
        return self._rhs

    @rhs.setter
    def rhs(self, rhs):
        if isinstance(rhs, Expression):
            self._rhs = rhs.rhs
        else:
            self._rhs = Parser().parse(rhs)

    def __str__(self):
        return self.rhs_str

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.rhs_str)

    def _sympy_(self):
        return self.rhs

    @property
    def rhs_str(self):
        try:
            if self.rhs.is_Boolean:
                expr_str = self._unwrap_bool(self.rhs)
            else:
                expr_str = str(self.rhs)
        except AttributeError:
            # For expressions that have simplified to Python objects (e.g.
            # True, False,...)
            expr_str = str(self.rhs)
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
            expr_str = '!({})'.format(expr)
        else:
            expr_str = str(expr)
        return expr_str

    @property
    def rhs_cstr(self):
        rhs = self.expand_integer_powers(self.rhs)
        cstr = ccode(rhs, user_functions=self._cfunc_map)
        cstr = self.strip_L_from_rationals(cstr)
        return cstr

    @property
    def rhs_xml(self):
        rhs = self.expand_integer_powers(self.rhs)
        s = ccode(rhs, user_functions=self._random_map)
        s = self.strip_L_from_rationals(s)
        s = self._ccode_print_warn_re.sub('', s)
        s = self._multiple_whitespace_re.sub(' ', s)
        return s

    @property
    def rhs_symbols(self):
        try:
            return self.rhs.free_symbols
        except AttributeError:  # For expressions that have been simplified
            return []

    @property
    def rhs_symbol_names(self):
        return (self.symbol_to_str(s) for s in self.rhs_symbols)

    @property
    def rhs_funcs(self):
        try:
            return (type(f) for f in self.rhs.atoms(sympy.Function)
                    if type(f) not in Parser.inline_random_distributions())
        except AttributeError:  # For expressions that have been simplified
            return []

    @property
    def rhs_random_distributions(self):
        try:
            return (type(f) for f in self.rhs.atoms(sympy.Function)
                    if type(f) in Parser.inline_random_distributions())
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
            if isinstance(self.rhs, (bool, int, float, BooleanTrue,
                                     BooleanFalse)):
                val = self.rhs
            else:
                if self.rhs.is_Boolean:
                    try:
                        val = self.rhs.subs(kwargs)
                    except Exception:
                        raise NineMLUsageError(
                            "Incorrect arguments provided to expression ('{}')"
                            ": '{}'\n".format(
                                "', '".join(self.rhs_symbol_names),
                                "', '".join(list(kwargs.keys()))))
                else:
                    try:
                        val = self.rhs.evalf(subs=kwargs)
                    except Exception:
                        raise NineMLUsageError(
                            "Incorrect arguments provided to expression '{}'"
                            ": '{}' (expected '{}')\n".format(
                                self.rhs,
                                "', '".join(list(kwargs.keys())),
                                "', '".join(self.rhs_symbol_names)))
                    try:
                        val = float(val)
                    except TypeError:
                        try:
                            locals_dict = deepcopy(kwargs)
                            locals_dict.update(str_to_npfunc_map)
                            val = eval(str(val), {}, locals_dict)
                        except Exception:
                            raise NineMLUsageError(
                                "Could not evaluate expression: {}"
                                .format(self.rhs_str))
            return val
        return nineml_expression

    def rhs_suffixed(self, suffix='', prefix='', excludes=[]):
        """
        Return copy of expression with all free symols suffixed (or prefixed)
        """
        try:
            return self.rhs.xreplace(dict(
                (s, sympy.Symbol(prefix + str(s) + suffix))
                for s in self.rhs_symbols if str(s) not in excludes))
        except AttributeError:  # For rhs that have been simplified to floats
            assert float(self.rhs)
            return self.rhs

    def rhs_name_transform_inplace(self, name_map):
        """Replace atoms on the RHS with values in the name_map in place"""
        self._rhs = self.rhs_substituted(name_map)

    def rhs_substituted(self, name_map):
        """Replace atoms on the RHS with values in the name_map"""
        return self.rhs.xreplace(dict(
            (Parser().parse(old), Parser().parse(new))
            for old, new in name_map.items()))

    def subs(self, old, new):
        "Substitute 'old' expression for 'new' in the rhs of the expression"
        self._rhs = self._rhs.subs(old, new)

    def simplify(self):
        """
        Simplify the RHS of the expression
        (see http://docs.sympy.org/latest/tutorial/simplification.html)
        """
        self._rhs = sympy.simplify(self._rhs)
        return self

    def rhs_str_substituted(self, name_map={}, funcname_map={}):
        """
        Replaces names and function names. Deprecated
        """
        expr_str = str(self.rhs_substituted(name_map))
        for old, new in funcname_map.items():
            expr_str = re.sub(r'(?<!\w)({})\('.format(old), new, expr_str)
        expr_str = expr_str.replace('**', '^')
        return expr_str

    def __add__(self, other):
        return self.rhs + other

    def __sub__(self, other):
        return self.rhs - other

    def __mul__(self, other):
        return self.rhs * other

    def __truediv__(self, other):
        return self.rhs / other

    def __div__(self, other):
        return self.__truediv__(other)

    def __pow__(self, other):
        return self.rhs ** other

    def __and__(self, other):
        return self.rhs & other

    def __or__(self, other):
        return self.rhs | other

    def __invert__(self):
        return ~self.rhs

    def __neg__(self):
        return -self.rhs

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

    def __idiv__(self, expr):
        return self.__itruediv__(expr)

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

    @classmethod
    def expand_integer_powers(cls, expr):
        """
        Convert integer powers in an expression to Muls, e.g. a**3 => a*a*a.
        This is used when printing to C-style strings as it is more accurate.
        """
        if isinstance(expr, sympy.Basic):
            integer_pows = list(p for p in expr.atoms(sympy.Pow)
                                if (p.as_base_exp()[1].is_Integer and
                                    abs(p.as_base_exp()[1]) > 1))
            to_replace = {}
            for int_pow in integer_pows:
                base, expn = int_pow.as_base_exp()
                repl = sympy.Mul(*([base] * abs(expn)), evaluate=False)
                if expn < 0:
                    repl = sympy.Pow(repl, -1)
                to_replace[int_pow] = repl
            if to_replace:
                expr = cls._non_eval_xreplace(expr, to_replace)
        return expr

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
                if isinstance(expr, ExprCondPair):
                    return ExprCondPair(
                        cls._non_eval_xreplace(expr.args[0], rule),
                        cls._non_eval_xreplace(expr.args[1], rule))
                else:
                    return expr.func(*args, evaluate=False)
        return expr

    @classmethod
    def strip_L_from_rationals(cls, expr_str):
        """
        Strips the 'L' inserted by Sympy's ANSI C printer for rational
        numbers as it is not supported in all C-like simulators (namely HOC)
        """
        return cls._rationals_re.sub(r'\1/\2', expr_str)

    @classmethod
    def symbol_to_str(cls, symbol):
        return cls._strip_parens_re.sub(r'\1', str(symbol))


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

    def __div__(self, other):
        return self.__truediv__(other)

    def __pow__(self, other):
        return sympy.sympify(self) ** other

    def __and__(self, other):
        return sympy.sympify(self) & other

    def __or__(self, other):
        return sympy.sympify(self) | other

    def __invert__(self):
        return ~sympy.sympify(self)

    def __neg__(self):
        return -sympy.sympify(self)

    @property
    def symbol(self):
        return self._sympy_()


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


class ExpressionWithSimpleLHS(ExpressionSymbol, ExpressionWithLHS):

    """Represents a an equation with a simple left-hand-side.
    That is, a single symbol, for example 's = t+1'
    """

    nineml_attr = ('name', 'rhs')

    def __init__(self, lhs, rhs, assign_to_reserved=False):
        ExpressionWithLHS.__init__(self, rhs)
        if not is_single_symbol(lhs):
            err = 'Expecting a single symbol on the LHS; got: %s' % lhs
            raise NineMLUsageError(err)
        if not assign_to_reserved and not is_valid_lhs_target(lhs):
            err = 'Invalid LHS target: %s' % lhs
            raise NineMLUsageError(err)
        self._name = validate_identifier(lhs)

    @property
    def name(self):
        return self._name

    def __str__(self):
        return '{} := {}'.format(self.lhs, self.rhs_str)

    def __repr__(self):
        return "{}(lhs='{}', rhs=({}))".format(self.__class__.__name__,
                                               self.lhs, self.rhs_str)

    @property
    def lhs(self):
        return self.name

    @property
    def lhs_atoms(self):
        return [self.lhs]

    def lhs_name_transform_inplace(self, name_map):
        self._name = name_map.get(self.lhs, self.lhs)


class ODE(ExpressionWithLHS):
    """
    An ordinary, first order differential equation.

    .. note::

        These should not be created directly, this class is
        used as base class for ``TimeDerivative``
    """

    def __init__(self, dependent_variable, independent_variable, rhs):
        ExpressionWithLHS.__init__(self, rhs)

        self._dependent_variable = validate_identifier(dependent_variable)
        self._independent_variable = validate_identifier(independent_variable)

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


from .utils import str_to_npfunc_map, is_single_symbol, is_valid_lhs_target  # @IgnorePep8
