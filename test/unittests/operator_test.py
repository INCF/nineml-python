import unittest
from string import ascii_lowercase
from itertools import chain, cycle, repeat
import traceback
import math
from nineml.values import SingleValue, ArrayValue, RandomValue
from operator import (
    add, sub, mul, truediv, div, pow, floordiv, mod, neg, iadd, idiv,
    ifloordiv, imod, imul, ipow, isub, itruediv, and_, or_, inv)
from nineml.utils.testing.comprehensive import instances_of_all_types
import numpy  # This is only imported here in the test as it is not dependency
from sympy import sympify, Basic as SympyBaseClass, Symbol
from nineml.abstraction.expressions import Expression, Alias
from nineml import units as un

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
        pow, truediv, sub, pow, neg, add, pow, div, truediv, truediv, add, pow,
        neg, div, truediv, mul, mul, div, mul, pow, neg, add, add, mul,
        truediv, sub, div, add, neg, sub, sub, sub, neg, mul, div]
    logical_ops = [and_, or_, inv, or_, inv, or_, and_]
    iops = [iadd, idiv, imul, ipow, isub, itruediv]

    named_expressions = list(chain(*(
        instances_of_all_types[t] for t in ('Alias', 'StateAssignment'))))
    logical_expressions = instances_of_all_types['Trigger']
    anonymous_expressions = instances_of_all_types['TimeDerivative']
    expressions = list(chain(named_expressions, anonymous_expressions))

    def test_anonymous_expression_operators(self):
        result = Expression('a + b')  # Arbitrary starting expression
        expr_iter = cycle(self.anonymous_expressions)
        for op in self.ops:
            if op in uniary_ops:
                ss_result = op(result.rhs)
                ee_result = op(result)
                op_str = ("{}({})".format(op.__name__, result))
            else:
                expr = next(expr_iter)
                if op in div_ops and expr.rhs == sympify(0.0):
                    expr = sympify(0.1)
                ss_result = op(result.rhs, expr.rhs)
                ee_result = op(result, expr)
                es_result = op(result, expr.rhs)
                se_result = op(result.rhs, expr)
                op_str = ("{}({}, {})".format(op.__name__, result, expr))
                self.assertEqual(
                    es_result, ss_result,
                    op_str + " not equal between Expression and sympy")
                self.assertEqual(
                    se_result, ss_result,
                    "{} not equal between Expression ({}) and sympy ({})"
                    .format(op_str, se_result, ss_result))
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
            result = Expression(ee_result)

    def test_named_expression_operators(self):
        result = Alias('a', 'a + b')  # Arbitrary starting expression
        expr_iter = cycle(self.named_expressions)
        alpha_iter = cycle(ascii_lowercase)
        for op in self.ops:
            if op in uniary_ops:
                ss_result = op(Symbol(result.name))
                ee_result = op(result)
                op_str = ("{}({})".format(op.__name__, result))
            else:
                expr = next(expr_iter)
                if op in div_ops and expr.rhs == sympify(0.0):
                    expr = sympify(0.1)
                ss_result = op(Symbol(result.name), Symbol(expr.name))
                ee_result = op(result, expr)
                es_result = op(result, Symbol(expr.name))
                se_result = op(Symbol(result.name), expr)
                op_str = ("{}({}, {})".format(op.__name__, result, expr))
                self.assertEqual(
                    es_result, ss_result,
                    "{} not equal between Expression ({}) and sympy ({})"
                    .format(op_str, es_result, ss_result))
                self.assertEqual(
                    se_result, ss_result,
                    "{} not equal between Expression ({}) and sympy ({})"
                    .format(op_str, se_result, ss_result))
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
            next_name = next(alpha_iter)
            if next_name == 't':
                next_name = next(alpha_iter)
            result = Alias(next_name, ee_result)

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
            result = ee_result

    def test_expression_logical_operators(self):
        result = Expression('a > b')  # Arbitrary starting expression
        expr_iter = iter(list(self.logical_expressions) * 10)
        for op in self.logical_ops:
            if op in uniary_ops:
                ss_result = op(result.rhs)
                ee_result = op(result)
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
                self.assertIsInstance(es_result, SympyBaseClass,
                                      op_str + " did not return a Expression")
                self.assertIsInstance(se_result, SympyBaseClass,
                                      op_str + " did not return a Expression")
                self.assertEqual(
                    sympify(es_result), ss_result,
                    op_str + " not equal between Expression and sympy")
                self.assertEqual(
                    sympify(se_result), ss_result,
                    op_str + " not equal between Expression and sympy")
            self.assertIsInstance(ee_result, SympyBaseClass,
                                  op_str + " did not return a Expression")
            self.assertEqual(
                ee_result, ss_result,
                "{} not equal between Expression ({}) and sympy ({})"
                .format(op_str, ee_result, ss_result))
            result = Expression(ee_result)


class TestUnits(unittest.TestCase):

    ops = [pow, mul, div, truediv, mul, truediv, pow, mul, div, div, pow]

    def test_dimension_operators(self):
        result = un.dimensionless  # Arbitrary starting expression
        dim_iter = cycle(instances_of_all_types['Dimension'])
        val_iter = cycle(instances_of_all_types['SingleValue'])
        for op in self.ops:
            if op is pow:
                val = int(next(val_iter) * 10)
                # Scale the value close to 10 to avoid overflow errors
                if val != 0.0:
                    val = val / 10 ** round(numpy.log10(abs(val)))
                dim = np_dim = int(val)
            else:
                dim = next(dim_iter)
                np_dim = 10 ** self._np_array(dim)
            np_result = numpy.log10(op(10 ** self._np_array(result),
                                       np_dim))
            new_result = op(result, dim)
            op_str = ("{}({}, {})".format(op.__name__, result, dim))
            self.assertIsInstance(result, un.Dimension,
                                  op_str + " did not return a Dimension")
            self.assertTrue(
                all(self._np_array(new_result) == np_result),
                "{} not equal between Dimension ({}) and numpy ({})"
                .format(op_str, self._np_array(new_result), np_result))
            result = new_result

    @classmethod
    def _np_array(self, dim):
        return numpy.array(list(dim), dtype=float)

    def test_unit_unit_operators(self):
        result = un.unitless  # Arbitrary starting expression
        unit_iter = cycle(instances_of_all_types['Unit'])
        val_iter = cycle(instances_of_all_types['SingleValue'])
        for op in self.ops:
            if op is pow:
                val = int(next(val_iter) * 10)
                # Scale the value close to 10 to avoid overflow errors
                if val != 0:
                    val = int(val / 10 ** round(numpy.log10(abs(val))))
                unit = dim = power = val
            else:
                unit = next(unit_iter)
                dim = unit.dimension
                power = 10 ** unit.power
            try:
                dim_result = op(result.dimension, dim)
                new_result = op(result, unit)
                power_result = numpy.log10(op(float(10 ** result.power),
                                              float(power)))
                op_str = ("{}({}, {})".format(op.__name__, result, unit))
                self.assertIsInstance(result, un.Unit,
                                      op_str + " did not return a Dimension")
                self.assertEqual(
                    new_result.dimension, dim_result,
                    "Dimension of {} not equal between Unit ({}) and explicit ({})"
                    .format(op_str, new_result.dimension, dim_result))
                self.assertEqual(
                    new_result.power, power_result,
                    "Power of {} not equal between Unit ({}) and explicit ({})"
                    .format(op_str, new_result.power, power_result))
                result = new_result
            except:
                traceback.print_exc()
                raise


class TestQuantities(unittest.TestCase):

    ops = [sub, sub, add, neg, truediv, mul, sub, mul, add, add, truediv, pow,
           neg, neg, mul, add, pow, neg, abs, add, div, abs, div, pow, sub,
           div, truediv, truediv, div, abs, neg, mul, abs, truediv, pow, sub,
           div, mul, pow, abs]
    matched_dim_ops = [add, sub]

    def test_quantities_operators(self):
        result = un.Quantity(1.0, un.unitless)  # Arbitrary starting expression
        val_iter = cycle(instances_of_all_types['SingleValue'])
        qty_iter = cycle(instances_of_all_types['Quantity'])
        for op in self.ops:
            if op in uniary_ops:
                if len(result.value):
                    f_result = [op(float(v)) for v in result.value]
                else:
                    f_result = op(float(result))
                q_result = op(result)
                units = result.units
                op_str = ("{}({})".format(op.__name__, result))
            else:
                if op is pow:
                    val = int(next(val_iter) * 10)
                    # Scale the value close to 10 to avoid overflow errors
                    if val != 0:
                        val = int(val / 10 ** round(numpy.log10(abs(val))))
                    qty = val
                    units = op(result.units, qty)
                    len_val = 0
                elif op in self.matched_dim_ops:
                    val = float(next(val_iter))
                    qty = val * result.units
                    units = result.units
                    len_val = 0
                else:
                    qty = next(qty_iter)
                    while qty.value.nineml_type == 'RandomValue':
                        qty = next(qty_iter)
                    val = qty.value
                    units = op(result.units, qty.units)
                    print units, qty
                    len_val = len(val)
                op_str = ("{}({}, {})".format(op.__name__, result, qty))
                if len(result.value):
                    if len_val:
                        # Get the first value as we can't use two
                        # array values together
                        val = next(iter(val))
                        qty = un.Quantity(val, units)
                        print qty
                    result_iter = (float(v) for v in result.value)
                    q_iter = repeat(float(val))
                    f_result = [op(r, q)
                                for r, q in zip(result_iter, q_iter)]
                elif len_val:
                    result_iter = repeat(float(result.value))
                    q_iter = (float(v) for v in val)
                    f_result = [op(r, q)
                                for r, q in zip(result_iter, q_iter)]
                else:
                    f_result = op(float(result.value), float(val))
                q_result = op(result, qty)
                op_str = ("{}({}, {})".format(op.__name__, result, qty))
                self.assertIsInstance(
                    q_result, un.Quantity,
                    "{} did not return a Quantity".format(op_str))
                if len(result.value) or len_val:
                    self.assertTrue(
                        all(numpy.array(q_result.value) ==
                            numpy.array(f_result)),
                        "Value of {} quantity not equal between Quantity "
                        "({}) and explicit ({})"
                        .format(op_str, f_result, val))
                else:
                    self.assertEqual(
                        float(q_result.value), f_result,
                        "Value of {} not equal between Quantity "
                        "({}) and explicit ({})"
                        .format(op_str, float(q_result.value), f_result))
                try:
                    self.assertEqual(
                        q_result.units, units,
                        "Units of {} (with {}:{} and {}:{}) not equal between "
                        "Quantity (dim={}, power={}) and explicit (dim={}, "
                        "power={})".format(
                            op_str, result.units.dimension, result.units.power,
                            (qty.units.dimension
                             if isinstance(qty, un.Quantity) else ''),
                            (qty.units.power
                             if isinstance(qty, un.Quantity) else ''),
                            q_result.units.dimension, q_result.units.power,
                            units.dimension, units.power))
                except:
                    traceback.print_exc()
                    raise
                result = q_result

#     def test_unit_operators(self):
#         result = un.unitless  # Arbitrary starting expression
#         unit_iter = cycle(instances_of_all_types['Unit'])
#         for op, unit in izip(self.ops, ):
#             unit = next(unit_iter)
#             while unit.offset == 0.0:  # Cannot use operators for offset units
#                 unit = next(unit_iter)
#             new_result = op(result, unit)
#             op_str = ("{}({}, {})".format(op.__name__, result, unit))
#             self.assertEqual(
#                 new_result, result,
#                 op_str + " not equal between Expression and sympy")
#             self.assertIsInstance(result, un.Unit,
#                                   op_str + " did not return a Expression")
#             result = new_result
