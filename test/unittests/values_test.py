import unittest
from nineml.values import SingleValue, ArrayValue, RandomValue
from operator import (
    add, sub, mul, truediv, div, divmod, pow, floordiv, mod, neg, abs, round)
from nineml.utils.testing.comprehensive import instances_of_all_types
# floor, ceil


class TestUnitsDimensions(unittest.TestCase):

    test_numbers = [0.86354992, 0.20872146, -0.66549436, -0.97101206,
                    -0.439105, 0.42909362, 0.73422364, 0.72300528,
                    -0.61679633, -0.38170423, 0.69437542, 0.45032681,
                    -0.71510604, 0.24341321, -0.67201598, 0.0982426,
                    -0.20864731, -0.06400868, 0.98941455, -0.62553766]

    operators = [add, sub, mul, truediv, div, divmod, pow, floordiv, mod, neg,
                 abs, round]

    def test_single_value_arithmetic(self):
        values = [SingleValue]