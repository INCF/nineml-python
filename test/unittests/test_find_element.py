import unittest
import nineml.units as un
from nineml.utils.comprehensive_example import ranDistrA, dynA, dynB, conA


class TestFindElement(unittest.TestCase):

    def test_find_dynamics(self):
        state_ass = dynB.regime('R1').on_event('ERP1').state_assignment('SV1')
        self.assertTrue(dynB.find(state_ass).object is state_ass)
        self.assertTrue(dynA.find(state_ass) is None)

    def test_find_rand_dist(self):
        param = ranDistrA.parameter('P1')
        self.assertEqual(ranDistrA.dimension_of(param), un.dimensionless)
        self.assertTrue(ranDistrA.find(param).object is param)
        self.assertEqual(ranDistrA.all_expressions, [])

    def test_conn_rule(self):
        param = conA.parameter('number')
        self.assertEqual(conA.dimension_of(param), un.dimensionless)
        self.assertTrue(conA.find(param).object is param)
        self.assertEqual(conA.all_expressions, [])
