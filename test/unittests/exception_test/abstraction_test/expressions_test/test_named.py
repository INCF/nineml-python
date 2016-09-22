import unittest
from nineml.abstraction.expressions.named import (Alias)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


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

