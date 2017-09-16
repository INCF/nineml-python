from builtins import str
import unittest
from nineml.abstraction import (
    Expression, Alias, StateAssignment, TimeDerivative, AnalogReducePort,
    AnalogReceivePort, Constant)
from nineml import units as un
from nineml.abstraction.expressions import (
    ExpressionWithSimpleLHS)
import sympy
from nineml.abstraction.expressions.utils import (
    is_single_symbol, str_expr_replacement)


class Expression_test(unittest.TestCase):

    def test_Valid(self):
        # rhs, expt_vars, expt_funcs, result, values
        valid_rhses = [
            (('a'), ('a'), (), 5, {'a': 5}),
            (('b'), ('b'), (), 7, {'b': 7}),
            (('a+b'), ('a', 'b'), (), 13, {'a': 12, 'b': 1}),
            (('1./(alpha+2*beta)'), ('alpha', 'beta'), (), 0.2,
             {'alpha': 1, 'beta': 2}),
        ]

        for rhs, exp_var, exp_func, exp_res, params in valid_rhses:
            e = Expression(rhs)
            self.assertEquals(set(e.rhs_symbol_names), set(exp_var))
            self.assertEquals(set(str(f) for f in e.rhs_funcs), set(exp_func))
            self.assertAlmostEqual(e.rhs_as_python_func(**params), exp_res,
                                   places=4)

        import numpy
        expr_vars = [
            ["-A/tau_r", ("A", "tau_r"), ()],
            ["V*V", ("V",), ()],
            ["a*(b*V - U)", ("U", "V", "b", "a"), ()],
            [" 0.04*V*V + 5.0*V + 1. + 140.0 - U + Isyn",
             ("V", "U", "Isyn"), ()],
            ["c", ("c"), ()],
            ["1", (), ()],
            ["atan2(sin(x),cos(y))", ("x", "y"),
             ("atan2", "sin", "cos")],
            ["1.*V", ("V"), ()],
            ["1.0", (), ()],
            [".1", (), ()],
            ["1/(1 + mg_conc*eta*exp(-1*gamma*V))", (
                "mg_conc", "eta", "gamma", "V"), ('exp',)],
            ["1 / ( 1 + mg_conc * eta *  exp( -1 * gamma*V))",
             ("mg_conc", "eta", "gamma", "V"), ('exp',)],
            ["1 / ( 1 + mg_conc * sin(0.5 * V) *  exp ( -1 * gamma*V))",
             ("mg_conc", "gamma", "V"), ('exp', "sin")],
            [".1 / ( 1.0 + mg_conc * sin(V) *  exp ( -1.0 * gamma*V))",
             ("mg_conc", "gamma", "V"), ('exp', "sin")],
            ["sin(w)", ("w"), ("sin",)]]

        namespace = {
            "A": 10.0,
            "tau_r": 11.0,
            "V": -70.0,
            "a": 1.2,
            "b": 3.0,
            "U": -80.0,
            "Isyn": 2.0,
            "c": 10.0,
            "mg_conc": 1.0,
            "eta": 2.0,
            "gamma": -20.0,
            "x": 1.0,
            "y": 1.0,
            "w": numpy.arange(10)
        }

        return_values = [-0.909090909091, 4900.0, -156.0, 69.0, 10.0, 1,
                         1.0, -70.0, 1.0, 0.1, 1.0, 1.0, 1.0, 0.1,
                         numpy.sin(namespace['w'])]

        for i, (expr, expt_vars, expt_funcs) in enumerate(expr_vars):
            c = Expression(expr)
            self.assertEqual(set(c.rhs_symbol_names), set(expt_vars))
            self.assertEqual(set(str(f) for f in c.rhs_funcs), set(expt_funcs))

            python_func = c.rhs_as_python_func
            param_dict = dict([(v, namespace[v]) for v in expt_vars])

            v = return_values[i] - python_func(**param_dict)
            self.assertAlmostEqual(numpy.dot(v, v), 0)

    def test_rhs_name_transform_inplace(self):
        # Signature: name(self, name_map)
                # Replace atoms on the RHS with values in the name_map

        e = Expression("V*sin(V)/(eta*mg_conc*exp(-V^2*gamma) + 1)")
        e.rhs_name_transform_inplace({'V': 'VNEW'})
        self.assertEquals(
            e.rhs_str, "VNEW*sin(VNEW)/(eta*mg_conc*exp(-VNEW^2*gamma) + 1)")

        # Don't Change builtin function names:
        e.rhs_name_transform_inplace({'sin': 'SIN'})
        self.assertEquals(
            e.rhs_str, "VNEW*sin(VNEW)/(eta*mg_conc*exp(-VNEW^2*gamma) + 1)")
        e.rhs_name_transform_inplace({'exp': 'EXP'})
        self.assertEquals(
            e.rhs_str, "VNEW*sin(VNEW)/(eta*mg_conc*exp(-VNEW^2*gamma) + 1)")

        # Check the attributes:
        self.assertEquals(set(e.rhs_atoms), set(
            ['VNEW', 'mg_conc', 'eta', 'gamma', 'exp', 'sin']))
        self.assertEquals(set(str(f) for f in e.rhs_funcs),
                          set(['exp', 'sin']))

    def test_escape_of_carets(self):
        self.assertEquals(Expression("a^2").rhs_cstr, 'a*a')
        self.assertEquals(Expression("(a - 2)^2").rhs_cstr,
                          '(a - 2)*(a - 2)')
        self.assertEquals(Expression("(a - (a - 2)^2.5)^2.5").rhs_cstr,
                          'pow(a - pow(a - 2, 2.5), 2.5)')
        self.assertEquals(Expression("a^(a - 2)").rhs_cstr, 'pow(a, a - 2)')


class C89ToSympy_test(unittest.TestCase):

    def setUp(self):
        self.a = sympy.Symbol('a')
        self.b = sympy.Symbol('b')
        self.c = sympy.Symbol('c')
        self.d = sympy.Symbol('d')
        self.e = sympy.Symbol('e')
        self.f = sympy.Symbol('f')
        self.g = sympy.Symbol('g')
        self.h = sympy.Symbol('h')
        self.i = sympy.Symbol('i')
        self.j = sympy.Symbol('j')

    def test_logical_and(self):
        expr = Expression('a && b')
        self.assertEqual(expr.rhs, sympy.And(self.a, self.b))

    def test_logical_or(self):
        expr = Expression('a || b')
        self.assertEqual(expr.rhs, sympy.Or(self.a, self.b))

    def test_equality(self):
        expr = Expression('a == b')
        self.assertEqual(expr.rhs, sympy.Eq(self.a, self.b))

    def test_equality_combined(self):
        expr = Expression('(a == b) && (c == d) || (e == f)')
        self.assertEqual(
            expr.rhs, sympy.Or(sympy.And(sympy.Eq(self.a, self.b),
                                         sympy.Eq(self.c, self.d)),
                               sympy.Eq(self.e, self.f)))

    def test_nested_relational(self):
        expr = Expression('((a == b) || (c == d)) && ((e == f) || (g < f))')
        self.assertEqual(
            expr.rhs, sympy.And(sympy.Or(sympy.Eq(self.a, self.b),
                                         sympy.Eq(self.c, self.d)),
                                sympy.Or(sympy.Eq(self.e, self.f),
                                         sympy.Lt(self.g, self.f))))

    def test_equality_nested_func(self):
        expr = Expression('((a == b) || (c == pow(d, 2))) && (e == f)')
        self.assertEqual(
            expr.rhs, sympy.And(sympy.Or(sympy.Eq(self.a, self.b),
                                         sympy.Eq(self.c, self.d ** 2)),
                                sympy.Eq(self.e, self.f)))

    def test_pow(self):
        expr = Expression('pow(a, b)')
        self.assertEqual(expr.rhs, self.a ** self.b)

    def test_negation(self):
        expr = Expression('!a')
        self.assertEqual(expr.rhs, sympy.Not(self.a))

    def test_double_negation(self):
        expr = Expression('!!a')
        self.assertEqual(expr.rhs, self.a)

    def test_triple_negation(self):
        expr = Expression('!!!a')
        self.assertEqual(expr.rhs, sympy.Not(self.a))


class SympyToC89_test(unittest.TestCase):

    def setUp(self):
        self.a = sympy.Symbol('a')
        self.b = sympy.Symbol('b')
        self.c = sympy.Symbol('c')
        self.d = sympy.Symbol('d')
        self.e = sympy.Symbol('e')
        self.f = sympy.Symbol('f')
        self.g = sympy.Symbol('g')
        self.h = sympy.Symbol('h')
        self.i = sympy.Symbol('i')
        self.j = sympy.Symbol('j')

    def test_logical_and(self):
        expr = Expression(sympy.And(self.a, self.b))
        self.assertEqual(expr.rhs_cstr, 'a && b')

    def test_logical_or(self):
        expr = Expression(sympy.Or(self.a, self.b))
        self.assertEqual(expr.rhs_cstr, 'a || b')

    def test_equality(self):
        expr = Expression(sympy.Eq(self.a, self.b))
        self.assertEqual(expr.rhs_cstr, 'a == b')

    def test_equality_combined(self):
        expr = Expression(sympy.Or(sympy.And(sympy.Eq(self.a, self.b),
                                             sympy.Eq(self.c, self.d)),
                                   sympy.Eq(self.e, self.f)))
        self.assertEqual(expr.rhs_cstr, 'a == b && c == d || e == f')

    def test_nested_relational(self):
        expr = Expression(sympy.And(sympy.Or(sympy.Eq(self.a, self.b),
                                             sympy.Eq(self.c, self.d)),
                                    sympy.Or(sympy.Eq(self.e, self.f),
                                             sympy.Lt(self.g, self.f))))
        self.assertEqual(
            expr.rhs_cstr, '(a == b || c == d) && (e == f || g < f)')

    def test_pow(self):
        expr = Expression(self.a ** self.b)
        self.assertEqual(expr.rhs_cstr, 'pow(a, b)')

    def test_negation(self):
        expr = Expression(sympy.Not(self.a))
        self.assertEqual(expr.rhs_cstr, '!a')

    def test_random(self):
        expr = Expression('random.exponential(a)')
        self.assertEqual(expr.rhs_cstr, 'random_exponential_(a)')


class SympifyTest(unittest.TestCase):

    def test_sympify(self):
        a = sympy.Symbol('a')
        self.assertEqual(a, sympy.sympify(Alias('a', 'b + c')))
        self.assertEqual(a, sympy.sympify(AnalogReceivePort('a')))
        self.assertEqual(a, sympy.sympify(AnalogReducePort('a')))
        self.assertEqual(a, sympy.sympify(Constant('a', 1.0,
                                                   units=un.unitless)))


class Rationals_test(unittest.TestCase):

    def test_xml(self):
        "Tests conversion of rationals back from the c-code version 1.0L/2.0L"
        expr = Expression('1/2')
        self.assertEqual(expr.rhs_xml, '1.0/2.0')

    def test_c89(self):
        "Tests conversion of rationals back from the c-code version 1.0L/2.0L"
        expr = Expression('1/2')
        self.assertEqual(expr.rhs_cstr, '1.0/2.0')

    def test_rationals_match(self):
        self.assertEqual(Expression.strip_L_from_rationals('aL/bL'), 'aL/bL')
        self.assertEqual(Expression.strip_L_from_rationals('a0L/bL'), 'a0L/bL')
        self.assertEqual(Expression.strip_L_from_rationals('aL/b0L'), 'aL/b0L')
        self.assertEqual(Expression.strip_L_from_rationals('a0L/b0L'),
                         'a0L/b0L')
        self.assertEqual(Expression.strip_L_from_rationals('aL/b0L'), 'aL/b0L')
        self.assertEqual(Expression.strip_L_from_rationals('1/2'), '1/2')
        self.assertEqual(Expression.strip_L_from_rationals('1L/2L'), '1/2')
        self.assertEqual(Expression.strip_L_from_rationals('1.0L/2.0L'),
                         '1.0/2.0')


class C89_test(unittest.TestCase):

    def test_logical_and(self):
        "Tests conversion of rationals back from the c-code version 1.0L/2.0L"
        expr = Expression('1/2')
        self.assertEqual(str(expr.rhs), '1/2')


# Testing Skeleton for class: ExpressionWithSimpleLHS
class ExpressionWithSimpleLHS_test(unittest.TestCase):

    def test_lhs(self):

        e = ExpressionWithSimpleLHS('a', 't+t+3 + sin(t) +q')

        self.assertEqual(list(e.lhs), ['a'])
        self.assertEqual(list(e.lhs_atoms), ['a'])
        self.assertEqual(sorted(list(e.rhs_atoms)), sorted(['t', 'sin', 'q']))
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 't', 'sin', 'q']))

        # RHS transform not affecting LHS:
        e.rhs_name_transform_inplace({'a': 'b'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 't', 'sin', 'q']))

        # LHS transform not affecting RHS:
        e.lhs_name_transform_inplace({'t': 'T'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 't', 'sin', 'q']))

        # name_transform affecting LHS & RHS:
        e.name_transform_inplace({'t': 'T'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 'T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.rhs_atoms)), sorted(['T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.lhs_atoms)), sorted(['a']))

        e.name_transform_inplace({'a': 'A'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['A', 'T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.rhs_atoms)), sorted(['T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.lhs_atoms)), sorted(['A']))


# Testing Skeleton for class: TimeDerivative
class TimeDerivative_test(unittest.TestCase):

    def test_atoms(self):
        td = TimeDerivative(variable='X',
                            rhs=' y * f - sin(q*q) + 4 * a * exp(Y)')
        self.assertEquals(sorted(td.atoms), sorted(
            ['X', 'y', 'f', 'sin', 'exp', 'q', 'a', 'Y', 't']))
        self.assertEquals(sorted(td.lhs_atoms), sorted(['X', 't']))
        self.assertEquals(sorted(td.rhs_atoms),
                          sorted(['y', 'f', 'sin', 'exp', 'q', 'a', 'Y']))

#   def test_dependent_variable(self):
    def test_independent_variable(self):
        td = TimeDerivative(variable='X',
                            rhs=' y*f - sin(q*q) + 4*a*exp(Y)')
        self.assertEquals(td.independent_variable, 't')
        self.assertEquals(td.variable, 'X')

        # Check substitutions to the LHS:
        td.lhs_name_transform_inplace({'X': 'x'})
        self.assertEquals(td.variable, 'x')

        # Since this is always time, we should not be changing the
        # independent_variable (dt)
        td.lhs_name_transform_inplace({'t': 'T'})
        self.assertEquals(td.independent_variable, 'T')

        # Aand change them again using 'name_transform_inplace'
        # Check substitutions to the LHS:
        td.name_transform_inplace({'x': 'X1'})
        self.assertEquals(td.variable, 'X1')

        # Since this is always time, we should not be changing the
        # independent_variable (dt)
        td.lhs_name_transform_inplace({'T': 'time'})
        self.assertEquals(td.independent_variable, 'time')


class MathUtils_test(unittest.TestCase):

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
        # from nineml.abstraction.component.util import MathUtil

        e = Alias.from_str('a := b*c + b1 + e_*exp(-12*g) + '
                           'd/(e*sin(f + g/e))')

        rhs_sub = e.rhs_substituted({'b': 'B', 'e': 'E'})
        self.assertEqual(
            rhs_sub,
            sympy.sympify('B*c + b1 + e_*exp(-12*g) + d/(E*sin(f + g/E))',
                          locals={'E': sympy.Symbol('E')}))

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

        e = Alias.from_str('a := b*c + d/(e_*sin(f+g/e_)) + b1 + '
                           'e_ / exp(12*g)')

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
        for expr_str, _ in Aliases:
            self.assertTrue(Alias.is_alias_str(expr_str))

        for expr_str, _ in TimeDerivatives:
            self.assertFalse(Alias.is_alias_str(expr_str))

        for expr_str, _ in Assignments:
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
