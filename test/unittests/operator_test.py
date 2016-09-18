import unittest
from itertools import chain, cycle
import math
from nineml.values import SingleValue, ArrayValue, RandomValue
from operator import (
    add, sub, mul, truediv, div, pow, floordiv, mod, neg, iadd, idiv,
    ifloordiv, imod, imul, ipow, isub, itruediv, and_, or_, inv)
from nineml.utils.testing.comprehensive import instances_of_all_types
import numpy  # This is only imported here in the test as it is not dependency
from sympy import sympify, Basic as SympyBaseClass
from nineml.abstraction.expressions import Expression, Alias

single_values = instances_of_all_types['SingleValue']

div_ops = (div, truediv, floordiv, mod, idiv, itruediv, imod)
uniary_ops = [neg, abs, inv]


class TestValues(unittest.TestCase):

    ops = [
        floordiv, pow, truediv, sub, pow, neg, mod, add, pow, floordiv, div,
        mod, mod, floordiv, truediv, truediv, abs, add, abs, pow, neg, div,
        truediv, mul, mul, div, mod, mul, abs, abs, pow, neg, add, floordiv,
        add, mul, truediv, sub, div, add, mod, neg, sub, floordiv, sub, sub,
        neg, mul, abs, div]

    iops = [iadd, idiv, ifloordiv, imod, imul, ipow, isub, itruediv]

    def test_conversions(self):
        for val in single_values:
            self.assertEqual(float(val), val._value)
            self.assertLess(float(val) - int(val), 1.0)

    def test_single_value_operators(self):
        result = SingleValue(10.5)  # Random starting value
        val_iter = cycle(single_values)
        for op in self.ops:
            if op in uniary_ops:
                ff_result = op(float(result))
                vv_result = op(result)
                op_str = ("{}({})".format(op.__name__, result))
            else:
                val = next(val_iter)
                if op in div_ops and float(val) == 0.0:
                    val = SingleValue(0.1)
                ff_result = op(float(result), float(val))
                vv_result = op(result, val)
                vf_result = op(result, float(val))
                fv_result = op(float(result), val)
                op_str = ("{}({}, {})".format(op.__name__, result, val))
                self.assertEqual(
                    float(vf_result), ff_result,
                    op_str + " not equal between single value and float")
                self.assertEqual(
                    float(fv_result), ff_result,
                    op_str + " not equal between single value and float")
                self.assertIsInstance(vf_result, SingleValue,
                                      op_str + " did not return a SingleValue")
                self.assertIsInstance(fv_result, SingleValue,
                                      op_str + " did not return a SingleValue")
            self.assertEqual(
                float(vv_result), ff_result,
                op_str + " not equal between single value and float")
            self.assertIsInstance(vv_result, SingleValue,
                                  op_str + " did not return a SingleValue")

    def test_array_value_operators(self):
        for array_val in instances_of_all_types['ArrayValue']:
            np_val = numpy.asarray(array_val)
            np_array_val = ArrayValue(numpy.asarray(array_val))
            val_iter = cycle(single_values)
            for op in self.ops:
                if op in uniary_ops:
                    vv_result = op(array_val)
                    nv_result = op(np_array_val)
                    np_result = op(np_val)
                    op_str = ("{}({})".format(op.__name__, array_val))
                else:
                    val = next(val_iter)
                    if op is pow:
                        # Negative numbers can't be raised to a fractional
                        # power so we avoid this by either using absolute
                        # values and scale back to sensible values to avoid
                        # overflow errors
                        array_val = abs(array_val)
                        np_array_val = abs(np_array_val)
                        np_val = abs(np_val)
                        val = abs(val) + 0.001
                        val = val / 10. ** round(math.log10(val))
                        val_scale = np_val.max() / 10.0
                        array_val = array_val * val_scale
                        np_array_val = np_array_val * val_scale
                        np_val = np_val * val_scale
                    elif op in div_ops:
                        # Ensure there are no zero values
                        array_val = array_val ** 2 + 1
                        np_array_val = np_array_val ** 2 + 1
                        np_val = np_val ** 2 + 1
                        val = val ** 2 + 1
                    vv_result = op(array_val, val)
                    vf_result = op(array_val, float(val))
                    nv_result = op(np_array_val, val)
                    nf_result = op(np_array_val, float(val))
                    np_result = op(np_val, float(val))
                    op_str = ("{}({}, {})".format(op.__name__, array_val, val))
                    rop_str = ("{}({}, {})".format(op.__name__, val,
                                                   array_val))
                    self.assertTrue(
                        all(numpy.asarray(vf_result) == np_result),
                        "{} not equal between array value ({}) and "
                        "numpy ({})".format(op_str, vf_result, np_result))
                    self.assertIsInstance(
                        vf_result, ArrayValue,
                        op_str + " did not return a ArrayValue")
                    self.assertTrue(
                        all(numpy.asarray(nf_result) == np_result),
                        "{} not equal between array value ({}) and "
                        "numpy ({})".format(op_str, nf_result, np_result))
                    self.assertIsInstance(
                        nf_result, ArrayValue,
                        "{} did not return a ArrayValue ({})"
                        .format(op_str, nf_result))
                    self.assertIsInstance(
                        nf_result._values, numpy.ndarray,
                        "{} did not maintain numpy _values in resultant "
                        "ArrayValue ({})"
                        .format(op_str, nf_result))
                    rvv_result = op(val, array_val)
                    rvf_result = op(float(val), array_val)
                    rnv_result = op(val, np_array_val)
                    rnf_result = op(float(val), np_array_val)
                    rnp_result = op(float(val), np_val)
                    self.assertTrue(
                        all(numpy.asarray(rvf_result) == rnp_result),
                        "{} not equal between array value ({}) and "
                        "numpy ({})".format(rop_str, rvf_result, rnp_result))
                    self.assertIsInstance(
                        rvf_result, ArrayValue,
                        rop_str + " did not return a ArrayValue")
                    self.assertTrue(
                        all(numpy.asarray(rnf_result) == rnp_result),
                        "{} not equal between array value ({}) and "
                        "numpy ({})".format(rop_str, rnf_result, rnp_result))
                    self.assertIsInstance(
                        rnf_result, ArrayValue,
                        "{} did not return a ArrayValue ({})"
                        .format(rop_str, rnf_result))
                    self.assertIsInstance(
                        rnf_result._values, numpy.ndarray,
                        "{} did not maintain numpy _values in resultant "
                        "ArrayValue ({})"
                        .format(rop_str, rnf_result))
                    self.assertTrue(
                        all(numpy.asarray(rvv_result) == rnp_result),
                        rop_str + " not equal between array value and numpy")
                    self.assertIsInstance(
                        rvv_result, ArrayValue,
                        rop_str + " did not return a ArrayValue")
                    self.assertTrue(
                        all(numpy.asarray(rnv_result) == rnp_result),
                        "{} not equal between array value ({}) and numpy ({})"
                        .format(rop_str, numpy.asarray(rnv_result),
                                rnp_result))
                    self.assertIsInstance(
                        rnv_result, ArrayValue,
                        rop_str + " did not return a ArrayValue")
                self.assertTrue(
                    all(numpy.asarray(vv_result) == np_result),
                    op_str + " not equal between array value and numpy")
                self.assertIsInstance(vv_result, ArrayValue,
                                      op_str + " did not return a ArrayValue")
                self.assertTrue(
                    all(numpy.asarray(nv_result) == np_result),
                    op_str + " not equal between array value and numpy")
                self.assertIsInstance(nv_result, ArrayValue,
                                      op_str + " did not return a ArrayValue")
                array_val = vv_result
                np_array_val = nv_result
                np_val = np_result

    def test_single_value_inline_operators(self):
        result = SingleValue(10.5)  # Random starting value
        for op, val in zip(self.iops, cycle(single_values)):
            if op in div_ops and float(val) == 0.0:
                val = SingleValue(0.1)
            ff_result = op(float(result), float(val))
            vv_result = op(result, val)
            vf_result = op(result, float(val))
            op_str = ("{}({}, {})".format(op.__name__, result, val))
            self.assertEqual(
                float(vf_result), ff_result,
                op_str + " not equal between single value and float")
            self.assertIsInstance(vf_result, SingleValue,
                                  op_str + " did not return a SingleValue")
            self.assertEqual(
                float(vv_result), ff_result,
                op_str + " not equal between single value and float")
            self.assertIsInstance(vv_result, SingleValue,
                                  op_str + " did not return a SingleValue")
            val = vv_result

    def test_array_value_inline_operators(self):
        for array_val in instances_of_all_types['ArrayValue']:
            np_val = numpy.asarray(array_val)
            np_array_val = ArrayValue(numpy.asarray(array_val))
            for i, (op, val) in enumerate(zip(
                    self.iops, cycle(single_values))):
                if op is ipow:
                    # Negative numbers can't be raised to a fractional
                    # power so we avoid this by either using absolute
                    # values and scale back to sensible values to avoid
                    # overflow errors
                    if i % 2:
                        array_val = abs(array_val)
                        np_array_val = abs(np_array_val)
                        np_val = abs(np_val)
                    else:
                        val = round(val)
                    val = val / 10. ** round(math.log10(abs(val)))
                elif op in div_ops and float(val) == 0.0:
                    val = SingleValue(0.1)
                vv_result = op(array_val, val)
                vf_result = op(array_val, float(val))
                nv_result = op(np_array_val, val)
                nf_result = op(np_array_val, float(val))
                np_result = op(np_val, float(val))
                op_str = ("{}({}, {})".format(op.__name__, array_val, val))
                self.assertTrue(
                    all(numpy.asarray(vf_result) == np_result),
                    "{} not equal between array value ({}) and "
                    "numpy ({})".format(op_str, vf_result, np_result))
                self.assertIsInstance(
                    vf_result, ArrayValue,
                    op_str + " did not return a ArrayValue")
                self.assertTrue(
                    all(numpy.asarray(nf_result) == np_result),
                    "{} not equal between array value ({}) and "
                    "numpy ({})".format(op_str, nf_result, np_result))
                self.assertIsInstance(
                    nf_result, ArrayValue,
                    "{} did not return a ArrayValue ({})"
                    .format(op_str, nf_result))
                self.assertIsInstance(
                    nf_result._values, numpy.ndarray,
                    "{} did not maintain numpy _values in resultant "
                    "ArrayValue ({})"
                    .format(op_str, nf_result))
                self.assertTrue(
                    all(numpy.asarray(vv_result) == np_result),
                    op_str + " not equal between array value and numpy")
                self.assertIsInstance(
                    vv_result, ArrayValue,
                    op_str + " did not return a ArrayValue")
                self.assertTrue(
                    all(numpy.asarray(nv_result) == np_result),
                    op_str + " not equal between array value and numpy")
                self.assertIsInstance(
                    nv_result, ArrayValue,
                    op_str + " did not return a ArrayValue")
                array_val = vv_result
                np_array_val = nv_result
                np_val = np_result


class TestExpressions(unittest.TestCase):

    ops = [
        pow, truediv, sub, pow, neg, add, pow, div,
        truediv, truediv, abs, add, abs, pow, neg, div,
        truediv, mul, mul, div, mul, abs, abs, pow, neg, add,
        add, mul, truediv, sub, div, add, neg, sub, sub, sub,
        neg, mul, abs, div]
    logical_ops = [and_, or_, inv, or_, inv, or_, and_]
    iops = [iadd, idiv, imul, ipow, isub, itruediv]

    named_expressions = list(chain(*(
        instances_of_all_types[t] for t in ('Alias', 'StateAssignment'))))
    logical_expressions = instances_of_all_types['Trigger']
    anonymous_expressions = instances_of_all_types['TimeDerivative']
    expressions = list(chain(named_expressions, anonymous_expressions))

    def test_expression_operators(self):
        result = Expression('a + b')  # Arbitrary starting expression
        expr_iter = cycle(self.expressions)
        for op in self.ops:
            if op in uniary_ops:
                ss_result = op(result.rhs)
                se_result = op(result)
                op_str = ("{}({})".format(op.__name__, result))
            else:
                expr = next(expr_iter)
                if op in div_ops and expr.rhs == sympify(0.0):
                    expr = sympify(0.1)
                ss_result = op(result.rhs, expr.rhs)
                ee_result = op(result, expr)
                es_result = op(result, expr.rhs)
                se_result = op(expr.rhs, expr)
                op_str = ("{}({}, {})".format(op.__name__, result, expr))
                self.assertEqual(
                    es_result, ss_result,
                    op_str + " not equal between Expression and sympy")
                self.assertEqual(
                    se_result, ss_result,
                    op_str + " not equal between Expression and sympy")
                self.assertIsInstance(es_result, SympyBaseClass,
                                      op_str + " did not return a Expression")
                self.assertIsInstance(se_result, SympyBaseClass,
                                      op_str + " did not return a Expression")
            self.assertEqual(
                ee_result, ss_result,
                "{} not equal between Expression ({}) and sympy ({})"
                .format(op_str, ee_result, ss_result))
            self.assertIsInstance(ee_result, SympyBaseClass,
                                  op_str + " did not return a Expression")
            expr = Expression(ee_result)

    def test_expression_inline_operators(self):
        result = Alias('a', 'b + c')  # Arbitrary starting expression
        expr_iter = cycle(self.named_expressions)
        for op in self.iops:
            expr = next(expr_iter)
            if op in div_ops and expr.rhs == sympify(0.0):
                expr = sympify(0.1)
            ss_result = op(result.rhs, expr)
            ee_result = op(result, expr)
            op_str = ("{}({}, {})".format(op.__name__, result, expr))
            self.assertEqual(
                ee_result.rhs, ss_result,
                "{} not equal between expression ({}) and sympy ({})"
                .format(op_str, ee_result, ss_result))
            self.assertIsInstance(ee_result, Expression,
                                  op_str + " did not return a SingleValue")
            expr = ee_result

    def test_expression_logical_operators(self):
        result = Expression('a > b')  # Arbitrary starting expression
        expr_iter = iter(list(self.logical_expressions) * 10)
        for op in self.logical_ops:
            if op in uniary_ops:
                ss_result = op(result.rhs)
                se_result = op(result)
                op_str = ("{}({})".format(op.__name__, result))
            else:
                expr = next(expr_iter)
                if op in div_ops and expr.rhs == sympify(0.0):
                    expr = sympify(0.1)
                ss_result = op(result.rhs, expr.rhs)
                ee_result = op(result, expr)
                es_result = op(result, sympify(expr))
                se_result = op(sympify(result), expr)
                op_str = ("{}({}, {})".format(op.__name__, result, expr))
                self.assertEqual(
                    sympify(es_result), ss_result,
                    op_str + " not equal between Expression and sympy")
                self.assertEqual(
                    sympify(se_result), ss_result,
                    op_str + " not equal between Expression and sympy")
                self.assertIsInstance(es_result, SympyBaseClass,
                                      op_str + " did not return a Expression")
                self.assertIsInstance(se_result, SympyBaseClass,
                                      op_str + " did not return a Expression")
            self.assertEqual(
                ee_result, ss_result,
                "{} not equal between Expression ({}) and sympy ({})"
                .format(op_str, ee_result, ss_result))
            self.assertIsInstance(ee_result, SympyBaseClass,
                                  op_str + " did not return a Expression")
            expr = Expression(ee_result)