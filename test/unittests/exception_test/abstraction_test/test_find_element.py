import unittest
from nineml.utils.comprehensive_example import dynA, dynB


class TestFindElement(unittest.TestCase):

    def test_find_dynamics(self):
        state_ass = dynB.regime('R1').on_event('ERP1').state_assignment('SV1')
        self.assertTrue(dynB.find(state_ass) is state_ass)
        self.assertTrue(dynA.find(state_ass) is None)
