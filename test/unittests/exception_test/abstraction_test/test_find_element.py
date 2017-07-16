import unittest
from nineml.utils.testing.comprehensive import dynA, dynB


class TestFindElement(unittest.TestCase):

    def test_find_dynamics(self):
        state_ass = dynB.regime('R1').on_event('ERP1').state_assignment('SV1')
        self.assertTrue(dynB.find_element(state_ass))
        self.assertFalse(dynA.find_element(state_ass))
