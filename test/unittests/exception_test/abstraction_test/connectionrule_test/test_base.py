import unittest
from nineml.abstraction.connectionrule.base import (ConnectionRule)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestConnectionRuleExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 42
        message: Unrecognised connection rule library path '{}'. Available options are '{}'

        context:
        --------
    def __init__(self, name, standard_library, parameters=None,
                 document=None):
        super(ConnectionRule, self).__init__(
            name, parameters, document=document)
        # Convert to lower case
        if (not standard_library.startswith(self.standard_library_basepath) or
                standard_library[self._base_len:] not in self.standard_types):
        """

        connectionrule = next(instances_of_all_types['ConnectionRule'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            connectionrule.__init__,
            name=None,
            standard_library=None,
            parameters=None,
            document=None)

