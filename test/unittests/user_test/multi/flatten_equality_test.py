import unittest
from nineml.user.multi import MultiDynamics
from nineml.utils.comprehensive_example import instances_of_all_types


class TestFlattenEquality(unittest.TestCase):

    def test_multi_dyn_ids(self):
        for dyn in instances_of_all_types[MultiDynamics.nineml_type].values():
            flat = dyn.flatten(name=dyn.name)
            self.assertFalse(dyn.equals(flat))
            self.assertFalse(flat.equals(dyn))
            self.assertTrue(dyn.equals(flat, allow_flatten=True),
                            "Multi-dyn doesn't equal flattened:\n{}"
                            .format(dyn.find_mismatch(flat)))
            self.assertTrue(flat.equals(dyn, allow_flatten=True),
                            "Flattened doesn't equal Multi-dyn:\n{}"
                            .format(flat.find_mismatch(dyn)))
