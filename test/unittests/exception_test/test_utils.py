import unittest
from nineml.utils.iterables import expect_single
from nineml.exceptions import NineMLUsageError


class TestExceptions(unittest.TestCase):

    def test_expect_single_ninemlruntimeerror(self):
        """
        line #: 98
        message: Object not iterable
        """
        self.assertRaises(
            NineMLUsageError,
            expect_single,
            lst=[])
        self.assertRaises(
            NineMLUsageError,
            expect_single,
            lst=[1, 2])
        self.assertRaises(
            NineMLUsageError,
            expect_single,
            lst=1)
