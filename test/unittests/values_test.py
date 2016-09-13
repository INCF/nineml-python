import unittest
from nineml.values import SingleValue, ArrayValue, RandomValue
from operator import (
    add, sub, mul, truediv, div, pow, floordiv, mod, neg,
    iadd, iand, iconcat, idiv, ifloordiv, ilshift, imod, imul, inv, ior, ipow,
    irepeat, isub, itruediv, ixor)
from nineml.utils.testing.comprehensive import instances_of_all_types
import numpy


single_values = instances_of_all_types['SingleValue']


class TestUnitsDimensions(unittest.TestCase):

    ops = [
        floordiv, pow, truediv, sub, pow, neg, mod, add, pow, floordiv, div,
        mod, mod, floordiv, truediv, truediv, abs, add, abs, pow, neg, div,
        truediv, mul, mul, div, mod, mul, abs, abs, pow, neg, add, floordiv,
        add, mul, truediv, sub, div, add, mod, neg, sub, floordiv, sub, sub,
        neg, mul, abs, div]
    uniary_ops = [neg, abs]

    iops = [iadd, iand, iconcat, idiv, ifloordiv, ilshift, imod, imul, inv,
            ior, ipow, irepeat, isub, itruediv, ixor]

    def test_conversions(self):
        for val in single_values:
            self.assertEqual(float(val), val._value)
            self.assertLess(float(val) - int(val), 1.0)

    def test_single_value_operators(self):
        result = SingleValue(10.5)  # Random starting value
        val_iter = iter(list(single_values) * 10)
        for op in self.ops:
            if op in self.uniary_ops:
                ff_result = op(float(result))
                vv_result = op(result)
                op_str = ("{}({})".format(op.__name__, result))
            else:
                val = next(val_iter)
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
            val_iter = iter(list(single_values) * 10)
            for op in self.ops:
                if op in self.uniary_ops:
                    vv_result = op(array_val)
                    nv_result = op(np_array_val)
                    np_result = op(np_val)
                    op_str = ("{}({})".format(op.__name__, array_val))
                else:
                    val = next(val_iter)
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
                        op_str + " did not return a ArrayValue")
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
