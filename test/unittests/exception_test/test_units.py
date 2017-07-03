import unittest
from nineml.units import (Dimension, Unit, Quantity)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLDimensionError, NineMLNameError,
                               NineMLRuntimeError)
import nineml.units as un
# from nineml.document import Document
# from nineml.values import SingleValue


class TestDimensionExceptions(unittest.TestCase):

    def test_from_sympy_ninemlruntimeerror(self):
        """
        line #: 237
        message: Cannot convert '{}' dimension, must be 1 or sympy expression
        """
        self.assertRaises(
            NineMLRuntimeError,
            Dimension.from_sympy,
            expr=2)


class TestUnitExceptions(unittest.TestCase):

    def test_to_SI_units_str_exception(self):
        """
        line #: 306
        message: Cannot convert to SI units string as offset is not zero ({})
        """
        self.assertRaises(
            Exception,
            un.degC.to_SI_units_str)

    def test___mul___ninemlruntimeerror(self):
        """
        line #: 366
        message: Can't multiply units with nonzero offsets ({} and {})
        """
        self.assertRaises(
            NineMLRuntimeError,
            un.degC.__mul__,
            other=un.ms)
        self.assertRaises(
            NineMLRuntimeError,
            un.ms.__mul__,
            other=un.degC)

    def test___truediv___ninemlruntimeerror(self):
        """
        line #: 379
        message: Can't divide units with nonzero offsets ({} and {})
        """
        self.assertRaises(
            NineMLRuntimeError,
            un.degC.__truediv__,
            other=un.ms)
        self.assertRaises(
            NineMLRuntimeError,
            un.ms.__truediv__,
            other=un.degC)

    def test___pow___ninemlruntimeerror(self):
        """
        line #: 395
        message: Can't raise units to power with nonzero offsets ({})
        """
        self.assertRaises(
            NineMLRuntimeError,
            un.degC.__pow__,
            power=None)


class TestQuantityExceptions(unittest.TestCase):

    def test___init___exception(self):
        """
        line #: 450
        message: Units ({}) must of type <Unit>
        """
        self.assertRaises(
            Exception,
            Quantity,
            value=1.0,
            units=un.time)

    def test___getitem___ninemlruntimeerror(self):
        """
        line #: 482
        message: Cannot get item from random distribution
        """

        random_value = next(instances_of_all_types['RandomDistributionValue'].itervalues())
        qty = Quantity(random_value, un.ms)
        self.assertRaises(
            NineMLRuntimeError,
            qty.__getitem__,
            index=0)

    def test_set_units_ninemldimensionerror(self):
        """
        line #: 487
        message: Can't change dimension of quantity from '{}' to '{}'
        """

        qty = Quantity(1.0, un.ms)
        self.assertRaises(
            NineMLDimensionError,
            qty.set_units,
            units=un.mV)

    def test_in_units_ninemldimensionerror(self):
        """
        line #: 499
        message: Can't change convert quantity dimension from '{}' to '{}'
        """
        qty = Quantity(1.0, un.ms)
        self.assertRaises(
            NineMLDimensionError,
            qty.in_units,
            units=un.mV)
# 
#     def test_from_xml_ninemlnameerror(self):
#         """
#         line #: 532
#         message: Did not find definition of '{}' units in the current document.
#         """
#         element = E(Quantity.nineml_type,
#                     E(SingleValue.nineml_type, '1.0'),
#                     units='blah')
#         self.assertRaises(
#             NineMLNameError,
#             Quantity.from_xml,
#             element=element,
#             document=Document())

    def test__scaled_value_ninemldimensionerror(self):
        """
        line #: 593
        message: Cannot scale value as dimensions do not match ('{}' and '{}')
        """

        quantity = Quantity(1.0, un.um)
        self.assertRaises(
            NineMLDimensionError,
            quantity._scaled_value,
            qty=1.0 * un.nF)

    def test__scaled_value_ninemldimensionerror2(self):
        """
        line #: 602
        message: Can only add/subtract numbers from dimensionless quantities
        """

        quantity = 1.0 * un.A
        self.assertRaises(
            NineMLDimensionError,
            quantity._scaled_value,
            qty=1.0)

    def test_parse_ninemlruntimeerror(self):
        """
        line #: 636
        message: Cannot '{}' to nineml.Quantity (can only convert
        quantities.Quantity and numeric objects)
        """
        self.assertRaises(
            NineMLRuntimeError,
            Quantity.parse,
            qty='a')

