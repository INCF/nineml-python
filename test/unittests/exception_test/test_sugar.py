import unittest
from nineml.sugar import On
from nineml.exceptions import NineMLUsageError


class TestExceptions(unittest.TestCase):

    def test_On_ninemlruntimeerror(self):
        """
        line #: 44
        message: Unexpected Type for On() trigger: {} {}
        """
        self.assertRaises(
            NineMLUsageError,
            On,
            trigger=1.0,
            do=None,
            to=None)
