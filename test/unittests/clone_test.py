import unittest
from nineml.abstraction import Dynamics, ConnectionRule, RandomDistribution
from nineml.utils.comprehensive_example import instances_of_all_types
from nineml.visitors.cloner import Cloner


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
        prev_obj = None
        cloner = Cloner()
        for objs in instances_of_all_types.itervalues():
            for obj in objs.itervalues():
                # Skip temporary objects
                if type(obj).__name__.startswith('_'):
                    continue
                clone = obj.clone(cloner=cloner)
                if hasattr(clone, 'validate'):
                    clone.validate()
                self.assertNotEqual(id(clone), id(obj))
                obj_keys = set(obj.__dict__.keys())
                clone_keys = set(clone.__dict__.keys())
                self.assertEqual(
                    obj_keys, clone_keys,
                    "Not all attributes were copied to clone ({}) of {}"
                    .format("', '".join(obj_keys - clone_keys), obj))
                try:
                    self.assertEqual(obj, clone,
                                     "Clone of {} does not match original:\n{}"
                                     .format(obj, obj.find_mismatch(clone)))
                except:
                    obj.find_mismatch(clone)
                self.assertNotEqual(obj, prev_obj,
                                    "{} matches previous obj {} incorrectly")
                prev_obj = obj


if __name__ == '__main__':

    # Original
    multi_dyn = instances_of_all_types['MultiDynamics']['multiDynPropB_dynamics'].sub_component('multiA').component_class
    oc = multi_dyn.regime('R1___R1').on_condition(
        'SV1__e > P3__e')
    e = multi_dyn.sub_component('e').component_class
    e_port = e.event_send_port('ESP1')
    print "id(e_port): {}".format(id(e_port))
    pe = multi_dyn.event_send_port('ESP1__e')
    pe_port = pe.port
    print "id(pe_port): {}".format(id(pe_port))
    oe = oc.output_event('ESP1__e')
    oe_port = oe.port.port
    print "id(oe_port): {}".format(id(oe_port))

    # Clone
    multi_dyn_clone = multi_dyn.clone()
    e_clone = multi_dyn_clone.sub_component('e').component_class
    e_clone_port = e_clone.event_send_port('ESP1')
    print "id(e_clone_port): {}".format(id(e_clone_port))
    oc_clone = multi_dyn_clone.regime('R1___R1').on_condition(
        'SV1__e > P3__e')
    pe_clone = multi_dyn_clone.event_send_port('ESP1__e')
    pe_clone_port = pe_clone.port
    print "id(pe_clone_port): {}".format(id(pe_clone_port))
    oe_clone = oc_clone.output_event('ESP1__e')
    oe_clone_port = oe_clone.port.port
    print "id(oe_clone_port): {}".format(id(oe_clone_port))
    print oe
