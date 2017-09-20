import unittest
from nineml.user.multi import MultiDynamics
from nineml.utils.comprehensive_example import instances_of_all_types


class TestFlattenEquality(unittest.TestCase):

    def test_multi_dyn_ids(self):
        for dyn in instances_of_all_types[MultiDynamics.nineml_type].values():
            flat = dyn.flatten()
            self.assertFalse(dyn.equals(flat))
            self.assertFalse(flat.equals(dyn))
            self.assertTrue(dyn.equals(flat, allow_flatten=True))
            self.assertTrue(flat.equals(dyn, allow_flatten=True))
