import unittest
from nineml.abstraction.expressions.named import (Alias, Constant)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLDimensionError, NineMLRuntimeError)


class TestAliasExceptions(unittest.TestCase):

    def test_from_str_ninemlruntimeerror(self):
        """
        line #: 87
        message: errmsg

        context:
        --------
    def from_str(cls, alias_string):
        \"\"\"Creates an Alias object from a string\"\"\"
        if not cls.is_alias_str(alias_string):
            errmsg = "Invalid Alias: %s" % alias_string
        """

        self.assertRaises(
            NineMLRuntimeError,
            Alias.from_str,
            alias_string=None)


class TestConstantExceptions(unittest.TestCase):

    def test___init___ninemldimensionerror(self):
        """
        line #: 115
        message: Dimensions do not match between provided quantity ({}) and units ({})

        context:
        --------
    def __init__(self, name, value, units=None):
        BaseALObject.__init__(self)
        self._name = name
        if isinstance(value, Quantity):
            if units is None:
                self._value = float(value._value)
                self._units = value.units
            elif units.dimension == value.units.dimension:
                self._value = float(value._value * 10 ** (units.power -
                                                          value.units.power))
                self._units = units
            else:
        """

        constant = next(instances_of_all_types['Constant'].itervalues())
        self.assertRaises(
            NineMLDimensionError,
            constant.__init__,
            name=None,
            value=None,
            units=None)

