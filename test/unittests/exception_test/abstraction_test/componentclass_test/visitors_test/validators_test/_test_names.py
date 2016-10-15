import unittest
from nineml.abstraction.componentclass.visitors.validators.names import (LocalNameConflictsComponentValidator, DimensionNameConflictsComponentValidator)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestLocalNameConflictsComponentValidatorExceptions(unittest.TestCase):

    def test_check_conflicting_symbol_ninemlruntimeerror(self):
        """
        line #: 33
        message: Duplication of symbol found: {}

        context:
        --------
    def check_conflicting_symbol(self, symbol):
        if symbol in self.symbols:
        """

        localnameconflictscomponentvalidator = next(instances_of_all_types['LocalNameConflictsComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            localnameconflictscomponentvalidator.check_conflicting_symbol,
            symbol=None)


class TestDimensionNameConflictsComponentValidatorExceptions(unittest.TestCase):

    def test_check_conflicting_dimension_ninemlruntimeerror(self):
        """
        line #: 65
        message: err

        context:
        --------
    def check_conflicting_dimension(self, dimension):
        try:
            if dimension != self.dimensions[dimension.name]:
                err = ("Duplication of dimension name '{}' for differing "
                       "dimensions ('{}', '{}')"
                       .format(dimension.name, dimension,
                               self.dimensions[dimension.name]))
        """

        dimensionnameconflictscomponentvalidator = next(instances_of_all_types['DimensionNameConflictsComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            dimensionnameconflictscomponentvalidator.check_conflicting_dimension,
            dimension=None)

