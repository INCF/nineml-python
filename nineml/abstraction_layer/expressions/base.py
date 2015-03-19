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
    parse_expr as sympy_parse, standard_transformations, convert_xor)
from sympy.parsing.sympy_tokenize import NAME, OP
from sympy.printing import print_ccode
import operator
import re
# import math_namespace
from nineml.exceptions import NineMLRuntimeError, NineMLMathParseError

builtin_constants = set(['pi', 'true', 'false', 'True', 'False'])
builtin_functions = set([
    'exp', 'sin', 'cos', 'log', 'log10', 'pow', 'abs',
    'sinh', 'cosh', 'tanh', 'sqrt', 'mod', 'sum',
    'atan', 'asin', 'acos', 'asinh', 'acosh', 'atanh', 'atan2'])
reserved_symbols = set(['t'])


class Parser(object):
    # Escape all objects in sympy namespace that aren't defined in NineML
    # by predefining them as symbol names to avoid naming conflicts when
    # sympifying RHS strings.
    _to_escape = set(s for s in dir(sympy)
                     if s not in chain(builtin_constants,
                                       builtin_functions))
    _valid_funcs = set((sympy.And, sympy.Or, sympy.Not)) | builtin_functions
    _func_to_op_map = {sympy.Function('pow'): operator.pow}

    _escape_random_re = re.compile(r'(?<!\w)random\.(\w+) *\(')

    # Inline randoms are deprecated in favour of RandomVariable elements,
    # but included here to get Brunel model to work
    _builtin_randoms = {
        'random_uniform_': sympy.Function('random_uniform_'),
        'random_binomial_': sympy.Function('random_binomial_'),
        'random_poisson_': sympy.Function('random_poisson_'),
        'random_exponential_': sympy.Function('random_exponential_')}

    def __init__(self):
        self.escaped_names = set()

    def parse(self, expr):
        if isinstance(expr, sympy.Basic):
            self._check_valid_funcs(expr)
        elif isinstance(expr, basestring):
            try:
                # Inline randoms are deprecated but included to get Brunel
                # model to work
                expr = str(expr)
                expr = self._escape_random_re.sub(r'random_\1_(', expr)
                transformations = (
                    [self, convert_xor] + list(standard_transformations))
                expr = sympy_parse(expr, transformations=transformations,
                                   local_dict=self._builtin_randoms)
                expr = self._postprocess(expr)
            except Exception, e:
                raise NineMLMathParseError(
                    "Could not parse math-inline expression: {}\n\n{}"
                    .format(expr, e))
        else:
            raise ValueError("Cannot convert value '{}' of type '{}' to SymPy "
                             "expression".format(repr(expr), type(expr)))
        return expr

    def __call__(self, tokens, local_dict, global_dict):  # @UnusedVariable
        """
        Wrapper function so processor can be passed as a 'transformation'
        to the Sympy parser
        """
        return self._preprocess(tokens)

    def _preprocess(self, tokens):
        """
        Escapes symbols that correspond to objects in SymPy but are not
        reserved identifiers in NineML
        """
        result = []
        # Loop through single tokens
        for toknum, tokval in tokens:
            if toknum == NAME:
                # Escape non-reserved identifiers in 9ML that are reserved
                # keywords in Sympy
                if tokval in self._to_escape:
                    self.escaped_names.add(tokval)
                    tokval = self._escape(tokval)
                # Convert logical identities from ANSI to Python names
                elif tokval == 'true':
                    tokval = 'True'
                elif tokval == 'false':
                    tokval = 'False'
            # Handle multiple negations
            elif toknum == OP and tokval.startswith('!'):
                # NB: Multiple !'s are grouped into the one token
                assert all(t == '!' for t in tokval)
                if len(tokval) % 2:
                    tokval = '~'  # odd number of negation symbols
                else:
                    continue  # even number of negation symbols, cancel out
            result.append((toknum, tokval))
        new_result = []
        # Loop through pairwise combinations
        pair_iterator = izip(result[:-1], result[1:])
        for (toknum, tokval), (next_toknum, next_tokval) in pair_iterator:
            # Handle trivial corner cases where the logical identities
            # (i.e. True and False) are immediately negated (damn unit-
            # tests making things more complicated than the need to be!;),
            # as Sympy casts True and False to the Python native objects,
            # and then the '~' gets interpreted as a bitwise shift rather
            # than a negation. Solution: drop the negation sign and negate
            # manually.
            if ((toknum == OP and tokval == '~') and
                (next_toknum == NAME and
                 next_tokval in ('True', 'False'))):
                tokval = 'True' if next_tokval is 'False' else 'False'
                toknum = NAME
                next(pair_iterator)  # Skip the next iteration
            # Convert the ANSI C89 standard for logical
            # 'and' and 'or', '&&' or '||', to the Sympy format '&' and '|'
            elif ((toknum == OP and tokval in ('&', '|') and
                   next_toknum == OP and next_tokval == tokval)):
                next(pair_iterator)  # Skip the next iteration
            new_result.append((toknum, tokval))
        return new_result

    def _postprocess(self, expr):
        # Convert symbol names that were escaped to avoid clashes with in-built
        # Sympy functions back to their original form
        while self.escaped_names:
            name = self.escaped_names.pop()
            expr = expr.xreplace(
                {sympy.Symbol(self._escape(name)): sympy.Symbol(name)})
        # Convert ANSI C functions to corresponding operator (i.e. 'pow')
        expr = self._func_to_op(expr)
        return expr

    @classmethod
    def _escape(self, s):
        return s + '__escaped__'

    @classmethod
    def _func_to_op(self, expr):
        if isinstance(expr, sympy.Function):
            args = (self._func_to_op(a) for a in expr.args)
            try:
                expr = self._func_to_op_map[type(expr)](*args)
            except KeyError:
                expr = expr.__class__(*args)
        return expr

    @classmethod
    def _check_valid_funcs(cls, expr):
        if isinstance(expr, sympy.Function):
            if type(expr) not in cls._valid_funcs:
                raise NineMLMathParseError(
                    "'{}' is a valid function in Sympy but not in 9ML"
                    .format(type(expr)))
            for arg in expr.args:
                cls._check_valid_funcs(arg)


class Expression(object):

    """ This is a base class for Expressions and Conditionals which provides
    the basic interface for parsing, yielding of python functions,
    C equivalents, name substitution """

    defining_attributes = ('rhs',)

    # Regular expression for extracting function names from strings (i.e. a
    # chain of valid identifiers follwed by an open parenthesis.
    _func_re = re.compile(r'(\w+) *\(')  # Match identifier followed by (
    _strip_parens_re = re.compile(r'^\(+(\w+)\)+$')  # Match if enclosed by ()
    _unescape_random_re = re.compile(r'(?<!\w)random_(\w+)_\(')

    def __repr__(self):
        return "{}(rhs='{}')".format(self.__class__.__name__, self.rhs_str)

    @classmethod
    def reserved_identifiers(cls):
        return chain(builtin_constants, builtin_functions,
                     reserved_symbols, Parser._builtin_randoms.iterkeys())

    def __init__(self, rhs):
        self.rhs = rhs

    def __eq__(self, other):
        return sympy.simplify(self.rhs - other.rhs) == 0

    @property
    def rhs(self):
        return self._rhs

    @rhs.setter
    def rhs(self, rhs):
        self._rhs = Parser().parse(rhs)

    @property
    def rhs_str(self):
        try:
            if self._rhs.is_Boolean:
                expr_str = self._unwrap_bool(self.rhs)
            else:
                expr_str = str(self._rhs)
        except AttributeError:  # For expressions that have simplified
            expr_str = str(self._rhs)
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
                if f not in Parser._builtin_randoms.itervalues())

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
