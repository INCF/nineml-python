import unittest
from nineml.abstraction.componentclass.visitors.validators.base import (BaseValidator)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import ()


class TestBaseValidatorExceptions(unittest.TestCase):

    def test_get_warnings_notimplementederror(self):
        """
        line #: 14
        message: 

        context:
        --------
    def get_warnings(self):
        """

        basevalidator = next(instances_of_all_types['BaseValidator'].itervalues())
        self.assertRaises(
            NotImplementedError,
            basevalidator.get_warnings)

