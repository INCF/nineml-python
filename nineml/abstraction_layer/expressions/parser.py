from __future__ import division
from itertools import chain, izip
import sympy
from sympy.parsing.sympy_parser import (
    parse_expr as sympy_parse, standard_transformations, convert_xor)
from sympy.parsing.sympy_tokenize import NAME, OP
import operator
import re
from nineml.exceptions import NineMLMathParseError

builtin_constants = set(['pi', 'true', 'false', 'True', 'False'])
builtin_functions = set([
    'exp', 'sin', 'cos', 'log', 'log10', 'pow', 'abs',
    'sinh', 'cosh', 'tanh', 'sqrt', 'mod', 'sum',
    'atan', 'asin', 'acos', 'asinh', 'acosh', 'atanh', 'atan2'])
reserved_symbols = set(['t'])

# Inline randoms are deprecated in favour of RandomVariable elements,
# but included here to get Brunel model to work
builtin_randoms = {
    'random_uniform_': sympy.Function('random_uniform_'),
    'random_binomial_': sympy.Function('random_binomial_'),
    'random_poisson_': sympy.Function('random_poisson_'),
    'random_exponential_': sympy.Function('random_exponential_')}


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
    _unescape_random_re = re.compile(r'(?<!\w)random_(\w+)_\(')
    _sympy_transforms = list(standard_transformations) + [convert_xor]

    def __init__(self):
        self.escaped_names = set()

    def parse(self, expr):
        if isinstance(expr, sympy.Basic):
            self._check_valid_funcs(expr)
        elif isinstance(expr, basestring):
            try:
                expr = self._escape_random_namespace(expr)
                expr = sympy_parse(
                    expr, transformations=[self] + self._sympy_transforms,
                    local_dict=builtin_randoms)
                expr = self._postprocess(expr)
            except Exception, e:
                raise NineMLMathParseError(
                    "Could not parse math-inline expression: {}\n\n{}"
                    .format(expr, e))
        else:
            raise TypeError("Cannot convert value '{}' of type '{}' to SymPy "
                            "expression".format(repr(expr), type(expr)))
        return expr

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

    def __call__(self, tokens, local_dict, global_dict):  # @UnusedVariable
        """
        Wrapper function so processor can be passed as a 'transformation'
        to the Sympy parser
        """
        return self._preprocess(tokens)

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
        if (isinstance(expr, sympy.Function) and
                type(expr) not in cls._valid_funcs):
            raise NineMLMathParseError(
                "'{}' is a valid function in Sympy but not in 9ML"
                .format(type(expr)))
        for arg in expr.args:
            cls._check_valid_funcs(arg)

    @classmethod
    def escape_random_namespace(cls, expr):
        """
        Inline randoms are deprecated but included to get Brunel
        model to work
        """
        return cls._escape_random_re.sub(r'random_\1_(', expr)

    @classmethod
    def unescape_random_namespace(cls, expr):
        """
        Inline randoms are deprecated but included to get Brunel
        model to work
        """
        return cls._unescape_random_re.sub(r'random.\1(', expr)

    @classmethod
    def reserved_identifiers(cls):
        return chain(builtin_constants, builtin_functions,
                     reserved_symbols, builtin_randoms.iterkeys())
