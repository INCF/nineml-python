from __future__ import print_function
import unittest
from nineml.abstraction import Dynamics, ConnectionRule, RandomDistribution
from nineml.utils.comprehensive_example import instances_of_all_types
from nineml.visitors.cloner import Cloner
from nineml.units import Unit, Dimension


class TestCloners(unittest.TestCase):

    def test_dynamics(self):
        for dyn in instances_of_all_types[Dynamics.nineml_type].values():
            clone = dyn.clone()
            self.assertNotEqual(id(dyn), id(clone))
            self.assertEqual(dyn, clone,
                             "Clone of '{}' Dynamics doesn't match original:\n"
                             "{}".format(dyn.name, dyn.find_mismatch(clone)))

    def test_connection_rule(self):
        for cr in instances_of_all_types[
                ConnectionRule.nineml_type].values():
            clone = cr.clone()
            self.assertNotEqual(id(cr), id(clone))
            self.assertEqual(cr, clone,
                             "Clone of '{}' Dynamics doesn't match original:\n"
                             "{}".format(cr.name, cr.find_mismatch(clone)))

    def test_random_distribution(self):
        for rd in instances_of_all_types[
                RandomDistribution.nineml_type].values():
            clone = rd.clone()
            self.assertNotEqual(id(rd), id(clone))
            self.assertEqual(rd, clone,
                             "Clone of '{}' Dynamics doesn't match original:\n"
                             "{}".format(rd.name, rd.find_mismatch(clone)))

    def test_instances_of_all_types(self):
        cloner = Cloner()
        for objs in instances_of_all_types.values():
            for obj in objs.values():
                # Skip temporary objects
                if obj.temporary:
                    continue
                clone = obj.clone(cloner=cloner)
                if hasattr(clone, 'validate'):
                    clone.validate()
                self.assertNotEqual(id(clone), id(obj))
                self.assertEqual(obj, clone,
                                 "Clone of {} does not match original:\n{}"
                                 .format(obj, obj.find_mismatch(clone)))
                if not isinstance(obj, (Unit, Dimension)):
                    for other_obj in objs.values():
                        if other_obj.id != obj.id:
                            self.assertNotEqual(
                                obj, other_obj,
                                ("{} matches previous obj {} incorrectly"
                                 .format(obj, other_obj)))
