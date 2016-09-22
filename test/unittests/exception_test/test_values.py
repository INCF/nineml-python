import unittest
from nineml.values import (ArrayValue, RandomValue)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestArrayValueExceptions(unittest.TestCase):

    def test___float___typeerror(self):
        """
        line #: 321
        message: ArrayValues cannot be converted to a single float

        context:
        --------
    def __float__(self):
        """

        arrayvalue = next(instances_of_all_types['ArrayValue'].itervalues())
        self.assertRaises(
            TypeError,
            arrayvalue.__float__)


class TestRandomValueExceptions(unittest.TestCase):

    def test___float___typeerror(self):
        """
        line #: 457
        message: RandomValues cannot be converted to a single float

        context:
        --------
    def __float__(self):
        """

        randomvalue = next(instances_of_all_types['RandomValue'].itervalues())
        self.assertRaises(
            TypeError,
            randomvalue.__float__)

    def test___iter___ninemlruntimeerror(self):
        """
        line #: 481
        message: Generator not set for RandomValue '{}'

        context:
        --------
    def __iter__(self):
        if self._generator is None:
        """

        randomvalue = next(instances_of_all_types['RandomValue'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            randomvalue.__iter__)

    def test_inverse_notimplementederror(self):
        """
        line #: 503
        message: 

        context:
        --------
    def inverse(self):
        """

        randomvalue = next(instances_of_all_types['RandomValue'].itervalues())
        self.assertRaises(
            NotImplementedError,
            randomvalue.inverse)

