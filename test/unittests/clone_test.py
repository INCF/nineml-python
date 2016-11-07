import unittest
from nineml.abstraction import Dynamics, ConnectionRule, RandomDistribution
from nineml.utils.testing.comprehensive import instances_of_all_types


class TestCloners(unittest.TestCase):

    def test_dynamics(self):
        for dyn in instances_of_all_types[Dynamics.nineml_type].itervalues():
            clone = dyn.clone()
            self.assertNotEqual(id(dyn), id(clone))
            self.assertEqual(dyn, clone,
                             "Clone of '{}' Dynamics doesn't match original:\n"
                             "{}".format(dyn.name, dyn.find_mismatch(clone)))

    def test_connection_rule(self):
        for cr in instances_of_all_types[
                ConnectionRule.nineml_type].itervalues():
            clone = cr.clone()
            self.assertNotEqual(id(cr), id(clone))
            self.assertEqual(cr, clone,
                             "Clone of '{}' Dynamics doesn't match original:\n"
                             "{}".format(cr.name, cr.find_mismatch(clone)))

    def test_random_distribution(self):
        for rd in instances_of_all_types[
                RandomDistribution.nineml_type].itervalues():
            clone = rd.clone()
            self.assertNotEqual(id(rd), id(clone))
            self.assertEqual(rd, clone,
                             "Clone of '{}' Dynamics doesn't match original:\n"
                             "{}".format(rd.name, rd.find_mismatch(clone)))

    def test_instances_of_all_types(self):
        prev_elem = None
        memo = {}
        for elems in instances_of_all_types.itervalues():
            for elem in elems.itervalues():
                clone = elem.clone(memo=memo)
                self.assertNotEqual(id(clone), id(elem))
                elem_keys = set(elem.__dict__.keys())
                clone_keys = set(clone.__dict__.keys())
                self.assertEqual(
                    elem_keys, clone_keys,
                    "Not all attributes were copied to clone ({}) of {}"
                    .format("', '".join(elem_keys - clone_keys), elem))
                self.assertEqual(elem, clone,
                                 "Clone of {} does not match original:\n{}"
                                 .format(elem, elem.find_mismatch(clone)))
                self.assertNotEqual(elem, prev_elem,
                                    "{} matches previous elem {}:\n{}"
                                    .format(elem, prev_elem,
                                            elem.find_mismatch(prev_elem)))

                prev_elem = elem
