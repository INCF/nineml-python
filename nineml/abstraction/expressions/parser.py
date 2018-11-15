from __future__ import division
from builtins import zip
from builtins import next
from builtins import range
from past.builtins import basestring
from builtins import object
from itertools import chain
import sympy
from sympy.parsing.sympy_parser import (
    parse_expr as sympy_parse, standard_transformations, convert_xor)
from tokenize import NAME, OP
import operator
import re
from nineml.exceptions import NineMLMathParseError
from .base import (
    builtin_constants, builtin_functions, reserved_symbols,
    reserved_identifiers)

# # Inline randoms are deprecated in favour of RandomVariable elements,
# # but included here to get Brunel model to work
# inline_random_distributions = set(('random.uniform', 'random.binomial',
#                                    'random.poisson', 'random.exponential'))


def sympy_func(func_name):
    return sympy.Function(func_name)


class Parser(object):
    # Escape all objects in sympy namespace that aren't defined in NineML
    # by predefining them as symbol names to avoid naming conflicts when
    # sympifying RHS strings.
    _to_escape = (set(dir(sympy)) -
                  set(chain(builtin_constants, builtin_functions)))
    _valid_funcs = set((sympy.And, sympy.Or, sympy.Not)) | builtin_functions
    _func_to_op_map = {sympy_func('pow'): operator.pow}
    _valid_identifier_re = re.compile(r'^[a-zA-Z_]\w*$')
    _escape_random_re = re.compile(r'(?<!\w)random\.(\w+)(?!\w)')
    _unescape_random_re = re.compile(r'(?<!\w)random_(\w+)_(?!\w)')
    _escape_empty_parens_re = re.compile(
        r'(?<!\w)random_(uniform|normal)_\(\)')
    _unescape_empty_parens_re = re.compile(
        r'(?<!\w)random_(uniform|normal)_\(0\)')
    _logic_relation_re = re.compile(r'(?:&|\||<|>|=)')
    # Matches logic and relational expressions, as well as parens and funcname(
    _tokenize_logic_re = re.compile(r'\s*(&{1,2}|\|{1,2}|<=?|>=?|==?|'
                                    r'(?:\w+|!|~)?\s*\(|\))\s*')
    # Matches function names+plus opening paren and just opening paren
    _left_paren_func_re = re.compile(r'(?:\w+|!|~)?\s*\(')
    _sympy_transforms = list(standard_transformations) + [convert_xor]
    _precedence = {'&&': 2, '&': 2, '|': 3, '||': 3, '>=': 1, '>': 1,
                   '<': 1, '<=': 1, '==': 1, '=': 1}
    _whitespace_re = re.compile(r'\s+')
    inline_randoms_dict = {
        'random_uniform_': sympy_func('random_uniform_'),
        'random_binomial_': sympy_func('random_binomial_'),
        'random_poisson_': sympy_func('random_poisson_'),
        'random_exponential_': sympy_func('random_exponential_'),
        'random_normal_': sympy_func('random_normal_')}

    def __init__(self):
        self.escaped_names = None

    def parse(self, expr):
        if isinstance(expr, (int, float)):
            pass
        elif isinstance(expr, sympy.Basic):
            self._check_valid_funcs(expr)
        elif self.valid_identifier(expr, safe_symbols=reserved_symbols):
            # Feeling lucky, first check we can get away with just converting
            # the expression into a symbol to avoid full parsing for trivial
            # cases
            expr = sympy.Symbol(expr)
        elif isinstance(expr, basestring):
            return self._parse_expr(expr)
        else:
            raise TypeError("Cannot convert value '{}' of type '{}' to "
                            " SymPy expression".format(repr(expr),
                                                       type(expr)))
        return expr

    def _parse_expr(self, expr):
        # Strip non-space whitespace
        expr = self._whitespace_re.sub(' ', expr)
        expr = self.escape_random_namespace(expr)
        if self._logic_relation_re.search(expr):
            expr = self._parse_relationals(expr)
        self.escaped_names = set()
        try:
            expr = sympy_parse(
                expr, transformations=([self] + self._sympy_transforms),
                local_dict=self.inline_randoms_dict)
        except Exception as e:
            raise NineMLMathParseError(
                "Could not parse math-inline expression: "
                "{}\n\n{}".format(expr, e))
        return self._postprocess(expr)

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
                # Convert logical identities from ANSI C -> Python names
                elif tokval == 'true':
                    tokval = 'True'
                elif tokval == 'false':
                    tokval = 'False'
                # Unescape relationals escaped in _parse_relationals
                elif tokval.endswith('__'):
                    tokval = tokval[:-2]
            # Handle C89 negations
            elif tokval == '!':
                toknum = OP
                tokval = '~'
            result.append((toknum, tokval))
        new_result = []
        # Loop through pairwise combinations
        pair_iterator = zip(result[:-1], result[1:])
        for (toknum, tokval), (next_toknum, next_tokval) in pair_iterator:
            # Handle trivial corner cases where the logical identities
            # (i.e. True and False) are immediately negated
            # as Sympy casts True and False to the Python native objects,
            # and then the '~' gets interpreted as a bitwise shift rather
            # than a negation.
            if toknum == OP and tokval == '~':
                if next_toknum == OP and next_tokval == '~':
                    # Skip this and the next iteration as the double negation
                    # cancels itself out
                    next(pair_iterator)
                    continue
                elif next_toknum == NAME and next_tokval in ('True', 'False'):
                    # Manually drop the negation sign and negate
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
        # Replace 'pow' functions with sympy '**'
        if isinstance(expr, sympy.Basic):
            expr = expr.replace(sympy_func('pow'), lambda b, e: b ** e)
            # Convert symbol names that were escaped to avoid clashes with in-
            # built Sympy functions back to their original form
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
    def valid_identifier(cls, expr, safe_symbols=set([])):
        if expr in reserved_identifiers - safe_symbols:
            return False
        return cls._valid_identifier_re.match(expr)

    @classmethod
    def _escape(self, s):
        return s + '__escaped__'

    @classmethod
    def _func_to_op(self, expr):
        """Maps functions to SymPy operators (i.e. 'pow')"""
        try:
            if expr.args:
                args = [self._func_to_op(a) for a in expr.args]
                try:
                    expr = self._func_to_op_map[type(expr)](*args)
                except KeyError:
                    expr = type(expr)(*args)
        except (AttributeError, TypeError):
            # for expr that have been converted to basic python types such as
            # int/floats/bools or sympy functions such as sin/cos/tan/etc...
            pass
        return expr

    @classmethod
    def _check_valid_funcs(cls, expr):
        """Checks if the provided Sympy function is a valid 9ML function"""
        if (isinstance(expr, sympy.Function) and
                str(type(expr)) not in chain(
                    cls._valid_funcs, iter(cls.inline_randoms_dict.keys()))):
            raise NineMLMathParseError(
                "'{}' is a valid function in Sympy but not in 9ML"
                .format(type(expr)))
        for arg in expr.args:
            cls._check_valid_funcs(arg)

    @classmethod
    def escape_random_namespace(cls, expr):
        expr = cls._escape_random_re.sub(r'random_\1_', expr)
        return cls._escape_empty_parens_re.sub(r'random_\1_(0)', expr)

    @classmethod
    def unescape_random_namespace(cls, expr):
        expr = cls._unescape_empty_parens_re.sub('random_\1_()', expr)
        return cls._unescape_random_re.sub(r'random.\1', expr)

    @classmethod
    def inline_random_distributions(cls):
        return iter(cls.inline_randoms_dict.values())

    @classmethod
    def _parse_relationals(cls, expr_string, escape='__'):
        """
        Based on shunting-yard algorithm
        (see http://en.wikipedia.org/wiki/Shunting-yard_algorithm)
        with modifications for skipping over non logical/relational operators
        and associated parentheses.
        """
        if isinstance(expr_string, bool):
            return expr_string
        # Splits and throws away empty tokens (between parens and operators)
        # and encloses the whole expression in parens
        tokens = (['('] +
                  [t for t in cls._tokenize_logic_re.split(expr_string.strip())
                   if t] + [')'])
        if len([1 for t in tokens
                if t.strip().endswith('(')]) != tokens.count(')'):
            raise NineMLMathParseError(
                "Unbalanced parentheses in expression: {}".format(expr_string))
        tokens = tokens
        operators = []  # stack (in SY algorithm terminology)
        operands = []  # output stream
        is_relational = []  # whether the current parens should be parsed
        # Num operands to concat when not parsing relation/bool. Because we are
        # also splitting on parenthesis, non-logic/relational expressions will
        # still be split on parenthesis and we need to keep track of how many
        # pieces they are in.
        num_args = [0]  # top-level should always be set to 1
        for tok in tokens:
            # If opening paren or function name + paren
            if cls._left_paren_func_re.match(tok):
                operators.append(tok)
                is_relational.append(False)
                num_args.append(0)
            # Closing paren.
            elif tok == ')':
                # Join together sub-expressions that have been split by parens
                # not used for relational/boolean expressions (e.g. functions)
                n = num_args.pop()
                if n > 1:
                    operands = operands[:-n] + [''.join(operands[-n:])]
                # If parens enclosed relat/logic (i.e. '&', '|', '<', '>', etc)
                if is_relational.pop():
                    # Get all the operators within the enclosing parens.
                    # Need to sort by order of precedence
                    try:
                        # Get index of last open paren
                        i = -1
                        while not cls._left_paren_func_re.match(operators[i]):
                            i -= 1
                    except IndexError:
                        raise NineMLMathParseError(
                            "Unbalanced parentheses in expression: {}"
                            .format(expr_string))
                    # Get lists of operators and operands at this level
                    # (i.e. after the last left paren)
                    level_operators = operators[(i + 1):]
                    level_operands = operands[i:]
                    # Pop these operators and operands off the list
                    # (along with the paren/function-call)
                    open_paren = operators[i]
                    operators = operators[:i]
                    operands = operands[:i]
                    while level_operators:
                        # Sort in order of precedence
                        prec = [cls._precedence[o] for o in level_operators]
                        i = sorted(list(range(len(prec))), key=prec.__getitem__)[0]
                        # Pop first operator
                        operator = level_operators.pop(i)
                        arg1, arg2 = (level_operands.pop(i),
                                      level_operands.pop(i))
                        if operator.startswith('&'):
                            func = "And{}({}, {})".format(escape, arg1, arg2)
                        elif operator.startswith('|'):
                            func = "Or{}({}, {})".format(escape, arg1, arg2)
                        elif operator.startswith('='):
                            func = "Eq{}({}, {})".format(escape, arg1, arg2)
                        elif operator == '<':
                            func = "Lt{}({}, {})".format(escape, arg1, arg2)
                        elif operator == '>':
                            func = "Gt{}({}, {})".format(escape, arg1, arg2)
                        elif operator == '<=':
                            func = "Le{}({}, {})".format(escape, arg1, arg2)
                        elif operator == '>=':
                            func = "Ge{}({}, {})".format(escape, arg1, arg2)
                        else:
                            assert False
                        level_operands.insert(i, func)
                    new_operand = level_operands[0]
                    if open_paren != '(':  # Function/logical negation
                        new_operand = open_paren + new_operand + ')'
                    operands.append(new_operand)
                # If parens enclosed something else
                else:
                    try:
                        # Apply the function/parens to the last operand
                        operands[-1] = operators.pop() + operands[-1] + ')'
                    except IndexError:
                        raise NineMLMathParseError(
                            "Unbalanced parentheses in expression: {}"
                            .format(expr_string))
                num_args[-1] += 1
            # If the token is one of ('&', '|', '<', '>', '<=', '>=' or '==')
            elif cls._tokenize_logic_re.match(tok):
                operators.append(tok)
                is_relational[-1] = True  # parse the last set of parenthesis
                # Check if there are more than one LHS sub-expr. to concatenate
                n = num_args[-1]
                if n == 0:
                    raise NineMLMathParseError(
                        "Logical/relational operator directly after a "
                        "parenthesis or start of expression: {}"
                        .format(expr_string))
                elif n > 1:
                    operands = operands[:-n] + [''.join(operands[-n:])]
                num_args[-1] = 0
            # If the token is an atom or a subexpr not containing any
            # logic/relational operators or parens.
            else:
                operands.append(tok)
                num_args[-1] += 1
        # After it is processed, operands should contain the parsed expression
        # as a single item
        return operands[0]
