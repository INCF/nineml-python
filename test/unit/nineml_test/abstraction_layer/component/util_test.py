

# Automatically Generated Testing Skeleton Template:
import unittest

from nineml.abstraction.dynamics import StateAssignment, TimeDerivative
from nineml.abstraction.expressions import Alias
from nineml.abstraction.expressions.utils import (
    is_single_symbol, str_expr_replacement)
import sympy

# Testing Skeleton for function:


# class Testparse(unittest.TestCase):
#
#    def test_parse(self):
# Signature: name(filename)
# Left over from orignal Version. This will be deprecated
# from nineml.abstraction.component.util import parse
#        warnings.warn('Tests not implemented')
# raise NotImplementedError()


# Testing Skeleton for class: MathUtil
class MathUtil_test(unittest.TestCase):

    def test_is_single_symbol(self):
        # Signature: name(cls, expr)
                # Returns ``True`` if the expression is a single symbol, possibly
                # surrounded with white-spaces
                #
                # >>> is_single_symbol('hello')
                # True
                #
                # >>> is_single_symbol('hello * world')
                # False

        self.assertTrue(is_single_symbol('t'))
        self.assertTrue(is_single_symbol('var_1'))
        self.assertTrue(is_single_symbol('var_long_name'))
        self.assertTrue(is_single_symbol('_myName'))

        self.assertFalse(is_single_symbol('r + y'))
        self.assertFalse(is_single_symbol('r+y'))
        self.assertFalse(is_single_symbol('sin(y)'))

    def test_get_rhs_substituted(self):
        # Signature: name(cls, expr_obj, namemap)
                # No Docstring
        # from nineml.abstraction.component.util import MathUtil

        e = Alias.from_str('a := b*c + b1 + e_*exp(-12*g) + d/(e*sin(f + g/e))')

        rhs_sub = e.rhs_substituted({'b': 'B', 'e': 'E'})
        self.assertEqual(
            str(rhs_sub), 'B*c + b1 + e_*exp(-12*g) + d/(E*sin(f + g/E))')

    def test_str_expr_replacement(self):
        # Signature: name(cls, frm, to, expr_string, func_ok=False)
                # replaces all occurences of name 'frm' with 'to' in expr_string
                # ('frm' may not occur as a function name on the rhs) ...
                # 'to' can be an arbitrary string so this function can also be used for
                # argument substitution.
                #
                # Returns the resulting string.
        # from nineml.abstraction.component.util import MathUtil
        t = 'b*c + d/(e*sin(f+g/e)) + b1 + e_ / exp(12*g)'

        t = str_expr_replacement('b', 'B', t)
        self.assertEqual(t, 'B*c + d/(e*sin(f+g/e)) + b1 + e_ / exp(12*g)')

        # 'e' is a builtin, so this function doesn't care.
        t = str_expr_replacement(frm='e', to='E', expr_string=t)
        self.assertEqual(t, 'B*c + d/(E*sin(f+g/E)) + b1 + e_ / exp(12*g)')

    def test_get_prefixed_rhs_string(self):
        # Signature: name(cls, expr_obj, prefix='', exclude=None)
                # No Docstring
        # from nineml.abstraction.component.util import MathUtil

        e = Alias.from_str('a := b*c + d/(e_*sin(f+g/e_)) + b1 + e_ / exp(12*g)')

        rhs_sub = e.rhs_suffixed(suffix='', prefix='U_', excludes=['c', 'e_'])
        self.assertEqual(
            rhs_sub,
            sympy.sympify('U_b*c + U_d/(e_*sin(U_f+U_g/e_)) + U_b1 +'
                          ' e_ / exp(12*U_g)')
        )


Aliases = [
    ("gB := 1/(eta*mg_conc*exp(-V*gamma) + 1)",
     ("gB", "1/(eta*mg_conc*exp(-V*gamma) + 1)")),
    ("g := gB*gmax*(-A + B)", ("g", "gB*gmax*(-A + B)")),
    (" dA := dt", ("dA", "dt")),
    (" h := dA/dx", ("h", "dA/dx"))
]


Assignments = [
    ("gB = 1/(eta*mg_conc*exp(-V*gamma) + 1)",
     ("gB", "1/(eta*mg_conc*exp(-V*gamma) + 1)")),
    ("g = gB*gmax*(-A + B)", ("g", "gB*gmax*(-A + B)")),
    (" dA = dt", ("dA", "dt")),
    (" h = dA/dx", ("h", "dA/dx"))]


TimeDerivatives = [
    ("dA_x/dt = -A/tau_r", ("A_x", "t", "-A/tau_r")),
    ("  dB/dt=-B/tau_d", ("B", "t", "-B/tau_d"))
]


class StrToExpr_test(unittest.TestCase):

    def test_is_alias(self):
        # Signature: name(cls, alias_string)
                # Returns True if the string could be an alias
        for expr_str, (exp_lhs, exp_rhs) in Aliases:
            self.assertTrue(Alias.is_alias_str(expr_str))

        for expr_str, (exp_dep, exp_indep, exp_rhs) in TimeDerivatives:
            self.assertFalse(Alias.is_alias_str(expr_str))

        for expr_str, (exp_lhs, exp_rhs) in Assignments:
            self.assertFalse(Alias.is_alias_str(expr_str))

    def test_alias(self):
        for expr_str, (exp_lhs, exp_rhs) in Aliases:
            alias = Alias.from_str(expr_str)

            self.assertEqual(alias.lhs, exp_lhs)
            self.assertEqual(str(alias.rhs), exp_rhs)

    def test_state_assignment(self):
        # Signature: name(cls, state_assignment_string)
                # No Docstring
        for expr_str, (exp_lhs, exp_rhs) in Assignments:
            ass = StateAssignment.from_str(expr_str)

            self.assertEqual(ass.lhs, exp_lhs)
            self.assertEqual(str(ass.rhs), exp_rhs)

    def test_time_derivative(self):
        # Signature: name(cls, time_derivative_string)
                # Creates an TimeDerivative object from a string
        for expr_str, (exp_dep, exp_indep, exp_rhs) in TimeDerivatives:
            td = TimeDerivative.from_str(expr_str)

            self.assertEquals(td.variable, exp_dep)
            self.assertEquals(td.independent_variable, exp_indep)
            self.assertEquals(str(td.rhs), str(exp_rhs))
