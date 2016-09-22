import unittest
from nineml.units import (Unit, Quantity)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLDimensionError, NineMLRuntimeError)


class TestUnitExceptions(unittest.TestCase):

    def test_to_SI_units_str_exception(self):
        """
        line #: 306
        message: Cannot convert to SI units string as offset is not zero ({})

        context:
        --------
    def to_SI_units_str(self):
        if self.offset != 0.0:
        """

        unit = next(instances_of_all_types['Unit'].itervalues())
        self.assertRaises(
            Exception,
            unit.to_SI_units_str)

    def test___mul___ninemlruntimeerror(self):
        """
        line #: 366
        message: Can't multiply units with nonzero offsets ({} and {})

        context:
        --------
    def __mul__(self, other):
        "self * other"
        try:
            if (self.offset != 0 or other.offset != 0):
        """

        unit = next(instances_of_all_types['Unit'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            unit.__mul__,
            other=None)

    def test___truediv___ninemlruntimeerror(self):
        """
        line #: 379
        message: Can't divide units with nonzero offsets ({} and {})

        context:
        --------
    def __truediv__(self, other):
        "self / expr"
        try:
            if (self.offset != 0 or other.offset != 0):
        """

        unit = next(instances_of_all_types['Unit'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            unit.__truediv__,
            other=None)

    def test___pow___ninemlruntimeerror(self):
        """
        line #: 395
        message: Can't raise units to power with nonzero offsets ({})

        context:
        --------
    def __pow__(self, power):
        "self ** expr"
        if self.offset != 0:
        """

        unit = next(instances_of_all_types['Unit'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            unit.__pow__,
            power=None)


class TestQuantityExceptions(unittest.TestCase):

    def test_set_units_ninemldimensionerror(self):
        """
        line #: 487
        message: Can't change dimension of quantity from '{}' to '{}'

        context:
        --------
    def set_units(self, units):
        if units.dimension != self.units.dimension:
        """

        quantity = next(instances_of_all_types['Quantity'].itervalues())
        self.assertRaises(
            NineMLDimensionError,
            quantity.set_units,
            units=None)

    def test_in_units_ninemldimensionerror(self):
        """
        line #: 499
        message: Can't change convert quantity dimension from '{}' to '{}'

        context:
        --------
    def in_units(self, units):
        \"\"\"
        Returns a float value in terms of the given units (dimensions must be
        equivalent)
        \"\"\"
        if units.dimension != self.units.dimension:
        """

        quantity = next(instances_of_all_types['Quantity'].itervalues())
        self.assertRaises(
            NineMLDimensionError,
            quantity.in_units,
            units=None)

    def test__scaled_value_ninemldimensionerror(self):
        """
        line #: 593
        message: Cannot scale value as dimensions do not match ('{}' and '{}')

        context:
        --------
    def _scaled_value(self, qty):
        try:
            if qty.units.dimension != self.units.dimension:
        """

        quantity = next(instances_of_all_types['Quantity'].itervalues())
        self.assertRaises(
            NineMLDimensionError,
            quantity._scaled_value,
            qty=None)

