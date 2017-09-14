from __future__ import division
import unittest
import nineml.units as un
from nineml.utils.comprehensive_example import ranDistrA


class RandomDistributionVisitorTests(unittest.TestCase):

    def test_basic_visitors(self):
        param = ranDistrA.parameter('P1')
        self.assertEqual(ranDistrA.dimension_of(param), un.dimensionless)
        self.assertTrue(ranDistrA.find(param) is param)
        self.assertEqual(ranDistrA.all_expressions, [])
