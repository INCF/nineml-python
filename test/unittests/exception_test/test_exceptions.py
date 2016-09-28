import unittest
from nineml.exceptions import (name_error)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLNameError)


class TestExceptions(unittest.TestCase):

    def test_accessor_with_handling_ninemlnameerror(self):
        """
        line #: 74
        message: '{}' {} does not have {} named '{}

        context:
        --------
def name_error(accessor):
    def accessor_with_handling(self, name):
        try:
            return accessor(self, name)
        except KeyError:
            # Get the name of the element type to be accessed making use of a
            # strict naming convention of the accessors
            type_name = ''.join(p.capitalize()
                                for p in accessor.__name__.split('_'))
        """
        class Dummy(object):
            nineml_type = 'Dummy'
            _name = 'dummy'

            @name_error
            def accessor(self, name):
                raise KeyError
        self.assertRaises(
            NineMLNameError,
            Dummy().accessor,
            name='a_name')
