import unittest
from nineml.exceptions import (name_error)
from nineml.utils.comprehensive_example import instances_of_all_types
from nineml.exceptions import (NineMLNameError)


class TestExceptions(unittest.TestCase):

    def test_accessor_with_handling_ninemlnameerror(self):
        """
        line #: 74
        message: '{}' {} does not have {} named '{}'
        """
        class Dummy(object):
            nineml_type = 'Dummy'
            key = 'dummy'

            @name_error
            def accessor(self, name):
                raise KeyError
        self.assertRaises(
            NineMLNameError,
            Dummy().accessor,
            name='a_name')
