from __future__ import division
import unittest
import nineml.units as un
from nineml.utils.testing.comprehensive import ranDistrA


class RandomDistributionVisitorTests(unittest.TestCase):

    def test_basic_visitors(self):
        param = ranDistrA.parameter('P1')
        self.assertEqual(ranDistrA.dimension_of(param), un.dimensionless)
        ranDistrA.assign_indices()  # Doesn't do anything at this stage
        self.assertTrue(ranDistrA.find_element(param))
        self.assertEqual(ranDistrA.all_expressions, [])
