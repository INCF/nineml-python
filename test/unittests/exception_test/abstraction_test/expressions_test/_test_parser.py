import unittest
from nineml.abstraction.expressions.parser import (Parser)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLMathParseError)


class TestParserExceptions(unittest.TestCase):

    def test_parse_typeerror(self):
        """
        line #: 63
        message: Cannot convert value '{}' of type '{}' to  SymPy expression

        context:
        --------
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
        """

        parser = next(instances_of_all_types['Parser'].itervalues())
        self.assertRaises(
            TypeError,
            parser.parse,
            expr=None)

    def test__parse_expr_ninemlmathparseerror(self):
        """
        line #: 80
        message: Could not parse math-inline expression: {}

{}

        context:
        --------
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
        except Exception, e:
        """

        parser = next(instances_of_all_types['Parser'].itervalues())
        self.assertRaises(
            NineMLMathParseError,
            parser._parse_expr,
            expr=None)

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

    def test__parse_relationals_ninemlmathparseerror2(self):
        """
        line #: 266
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
        """

        self.assertRaises(
            NineMLMathParseError,
            Parser._parse_relationals,
            expr_string=None,
            escape='__')

    def test__parse_relationals_ninemlmathparseerror3(self):
        """
        line #: 313
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
                        i = sorted(range(len(prec)), key=prec.__getitem__)[0]
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
        """

        self.assertRaises(
            NineMLMathParseError,
            Parser._parse_relationals,
            expr_string=None,
            escape='__')

    def test__parse_relationals_ninemlmathparseerror4(self):
        """
        line #: 324
        message: Logical/relational operator directly after a parenthesis or start of expression: {}

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
                        i = sorted(range(len(prec)), key=prec.__getitem__)[0]
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
        """

        self.assertRaises(
            NineMLMathParseError,
            Parser._parse_relationals,
            expr_string=None,
            escape='__')

