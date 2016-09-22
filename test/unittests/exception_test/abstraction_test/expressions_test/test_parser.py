import unittest
from nineml.abstraction.expressions.parser import (Parser)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLMathParseError)


class TestParserExceptions(unittest.TestCase):

    def test__check_valid_funcs_ninemlmathparseerror(self):
        """
        line #: 197
        message: '{}' is a valid function in Sympy but not in 9ML

        context:
        --------
    def _check_valid_funcs(cls, expr):
        \"\"\"Checks if the provided Sympy function is a valid 9ML function\"\"\"
        if (isinstance(expr, sympy.Function) and
                str(type(expr)) not in chain(
                    cls._valid_funcs, cls.inline_randoms_dict.iterkeys())):
        """

        self.assertRaises(
            NineMLMathParseError,
            Parser._check_valid_funcs,
            expr=None)

    def test__parse_relationals_ninemlmathparseerror(self):
        """
        line #: 232
        message: Unbalanced parentheses in expression: {}

        context:
        --------
    def _parse_relationals(cls, expr_string, escape='__'):
        \"\"\"
        Based on shunting-yard algorithm
        (see http://en.wikipedia.org/wiki/Shunting-yard_algorithm)
        with modifications for skipping over non logical/relational operators
        and associated parentheses.
        \"\"\"
        if isinstance(expr_string, bool):
            return expr_string
        # Splits and throws away empty tokens (between parens and operators)
        # and encloses the whole expression in parens
        tokens = (['('] +
                  [t for t in cls._tokenize_logic_re.split(expr_string.strip())
                   if t] + [')'])
        if len([1 for t in tokens
                if t.strip().endswith('(')]) != tokens.count(')'):
        """

        self.assertRaises(
            NineMLMathParseError,
            Parser._parse_relationals,
            expr_string=None,
            escape='__')

