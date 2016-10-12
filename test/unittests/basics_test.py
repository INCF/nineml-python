import collections
import unittest
from nineml.utils.testing.comprehensive import (
    all_types, instances_of_all_types)
from nineml.abstraction.ports import SendPortBase
from nineml.base import pluralise
from nineml.user.multi import append_namespace
from numpy import sum, product
import re


class TestAccessors(unittest.TestCase):

    defattr_prop_exceptions = [
        (re.compile(r'(Analog|Event)(Send|Reduce|Receive)PortExposure'),
         re.compile(r'_name')),
        (re.compile(r'(Event|Analog)PortConnection'),
         re.compile(r'_(sender|receiver)_(name|role)'))]

    def test_defining_attributes(self):
        for name, cls in all_types.iteritems():
            if hasattr(cls, 'defining_attributes'):
                for attr_name in cls.defining_attributes:
                    for elem in instances_of_all_types[name].itervalues():
                        if elem.__class__.__name__.startswith('_'):
                            continue  # Skip temporary objects
                        attr = getattr(elem, attr_name)
                        # Get corresponding property if present and it is not
                        # one of the exceptions
                        if not attr_name.startswith('_'):
                            continue
                        if not hasattr(cls, attr_name[1:]):
                            continue
                        if any(c.match(name) and a.match(attr_name)
                               for c, a in self.defattr_prop_exceptions):
                            continue
                        prop = getattr(elem, attr_name[1:])
                        if isinstance(prop, collections.Iterator):
                            continue
                        # If none of the above conditions are true then the
                        # accessor should be the same as the property
                        self.assertEqual(attr, prop,
                                         "'{}' in {} ({}) does not match "
                                         "property ({})".format(
                                             attr_name, elem, attr, prop))

    def test_member_accessors(self):
        """
        Each "ContainerObject" provides accessor methods for each member type
        it contains that return:
            - iterator over each member
            - iterator over the names of the members
            - accessor for an individual member using the name
            - number of members

        This test checks to see whether they are internally consistent and of
        the right type
        """
        for name, cls in all_types.iteritems():
            if hasattr(cls, 'class_to_member'):
                for elem in instances_of_all_types[name].values():
                    for member in cls.class_to_member:
                        num = elem._num_members(member, cls.class_to_member)
                        names = list(elem._member_keys_iter(
                            member, cls.class_to_member))
                        members = sorted(elem._members_iter(
                            member, cls.class_to_member))
                        accessor_members = sorted(
                            elem._member_accessor(member,
                                                  cls.class_to_member)(n)
                            for n in names)
                        # Check num_* matches number of members and names
                        self.assertIsInstance(
                            num, int, ("num_{} did not return an integer ({})"
                                       .format(cls.class_to_member[member],
                                               num)))
                        self.assertEqual(
                            len(members), num,
                            "num_{} did not return the same length ({}) as the"
                            " number of members ({})".format(
                                cls.class_to_member[member], num,
                                len(members)))
                        self.assertEqual(
                            len(names), num,
                            "num_{} did not return the same length ({}) as the"
                            " number of names ({})".format(
                                cls.class_to_member[member], num,
                                len(names)))
                        # Check all names are strings and don't contain
                        # duplicates
                        self.assertTrue(
                            all(isinstance(n, basestring) for n in names),
                            "Not all names of {} in '{} {} were strings "
                            "('{}')".format(member, elem.key, name,
                                            names))
                        self.assertEqual(
                            len(names), len(set(names)),
                            "Duplicate names found in {} members of '{}' {} "
                            "('{}')".format(member, elem.key, name, names))
                        # Check all members are of the correct type
                        self.assertTrue(
                            all(m.nineml_type == member for m in members),
                            "Not all {} members accessed in '{}' {} via "
                            "iterator were of {} type ({})"
                            .format(member, elem.key, name, member,
                                    ', '.join(str(m) for m in members)))
                        self.assertEqual(
                            members, accessor_members,
                            "{} members accessed through iterator ({}) do not "
                            "match members accessed through individual "
                            "accessor method ({}) for '{}' {}"
                            .format(member, members, accessor_members,
                                    elem.key, name))
                    total_num = elem.num_elements()
                    all_keys = list(elem.element_keys())
                    all_members = sorted(elem.elements())
                    all_accessor_members = sorted(
                        elem.element(n, include_send_ports=True)
                        for n in all_keys)
                    self.assertIsInstance(
                        total_num, int,
                        ("num_elements did not return an integer ({})"
                         .format(total_num)))
                    self.assertEqual(
                        len(all_members), total_num,
                        "num_elements did not return the same length "
                        "({}) as the number of all_members ({})".format(
                            total_num, len(all_members)))
                    # Check all all_keys are strings and don't contain
                    # duplicates
                    self.assertTrue(
                        all(isinstance(n, basestring) for n in all_keys),
                        "Not all element names in '{} {} were strings "
                        "('{}')".format(elem.key, name, all_keys))
                    self.assertEqual(
                        len(all_keys), len(set(all_keys)),
                        "Duplicate element names found in '{}' {} "
                        "('{}')".format(elem.key, name, all_keys))
                    # Check all all_members are of the correct type
                    self.assertGreaterEqual(
                        len(all_members), len(all_keys),
                        "The length of all members ({}) should be equal to or "
                        "greater than the length of member names ({}), which "
                        "wasn't the case for '{}' {}. NB: "
                        "send ports will be masked by state variables and "
                        "aliases".format(len(all_members), len(all_keys),
                                         elem.key, name))
                    diff = set(all_members) - set(all_accessor_members)
                    self.assertTrue(
                        all(isinstance(m, SendPortBase) for m in diff),
                        "Elements accessed through iterator ({}) do not "
                        "match all_members accessed through individual "
                        "accessor method ({}) for '{}' {}, with the exception "
                        "of send ports"
                        .format(all_members, all_accessor_members,
                                elem.key, name))

    def test_port_accessors(self):
        for cls_name in ('Dynamics', 'DynamicsProperties', 'MultiDynamics',
                         'MultiDynamicsProperties', 'Population', 'Selection',
                         'SubDynamics'):
            cls = all_types[cls_name]
            for elem in instances_of_all_types[cls_name].values():
                for prefix in ('', 'receive_', 'send_', 'analog_', 'event_',
                               'analog_receive_', 'event_receive_',
                               'analog_reduce_'):
                    num = getattr(elem, 'num_{}ports'.format(prefix))
                    names = list(getattr(elem, '{}port_names'.format(prefix)))
                    members = sorted(getattr(elem, '{}ports'.format(prefix)))
                    accessor_members = sorted(
                        getattr(elem, '{}port'.format(prefix))(n)
                        for n in names)
                    # Check num_* matches number of members and names
                    self.assertEqual(
                        len(members), num,
                        "num_{}ports did not return the same length ({}) as "
                        "the number of members ({})".format(prefix, num,
                                                            len(members)))
                    self.assertEqual(
                        len(names), num,
                        "num_{}ports did not return the same length ({}) as "
                        "the number of names ({})".format(prefix, num,
                                                          len(names)))
                    # Check all names are strings and don't contain
                    # duplicates
                    self.assertEqual(
                        len(names), len(set(names)),
                        "Duplicate names found in {}ports of '{}' {} "
                        "('{}')".format(prefix, elem.key, cls_name, names))
                    self.assertEqual(
                        members, accessor_members,
                        "{}ports accessed through iterator ({}) do not "
                        "match members accessed through individual "
                        "accessor method ({}) for '{}' {}"
                        .format(prefix, members, accessor_members,
                                elem.key, cls_name))

    def test_multi_dynamics_accessors(self):
        for class_name, mutli_class_name, non_ns_property in (
            (('Dynamics', 'MultiDynamics', 'component_class'),
             ('DynamicsProperties', 'MultiDynamicsProperties', 'component'))):
            cls = all_types[class_name]
            for elem in instances_of_all_types[mutli_class_name].values():
                flat_elem = elem.flatten()
                for accessor_name in cls.class_to_member.itervalues():
                    if accessor_name.endswith('_port'):
                        continue  # Already covered in previous test
                    all_sc_nums = []
                    all_sc_names = []
                    all_sc_members = []
                    for sub_comp in elem.sub_components:
                        comp = getattr(sub_comp, non_ns_property)
                        c_num = self._num_members(comp, accessor_name)
                        c_names = self._member_names(comp, accessor_name)
                        c_members = self._members(comp, accessor_name)
                        sc_num = self._num_members(sub_comp, accessor_name)
                        sc_names = self._member_names(sub_comp, accessor_name)
                        sc_members = self._members(sub_comp, accessor_name)
                        sc_acc_members = self._accessor_members(
                            sub_comp, accessor_name, sc_names)
                        self.assertEqual(sc_num, c_num)
                        self.assertEqual(sc_names,
                                         [append_namespace(n, sub_comp.name)
                                          for n in c_names])
                        self.assertEqual(c_members,
                                         [sc._object for sc in sc_members])
                        self.assertEqual(sc_members, sc_acc_members)
                        all_sc_nums.append(sc_num)
                        all_sc_names.extend(sc_names)
                        all_sc_members.extend(sc_members)
                    num = self._num_members(elem, accessor_name)
                    names = self._member_names(elem, accessor_name)
                    members = self._members(elem, accessor_name)
                    # Basic consistency checks
                    self.assertEqual(num, len(names))
                    self.assertEqual(num, len(members))
                    self.assertEqual(
                        members,
                        self._accessor_members(elem, accessor_name, names))
                    # Check with flatttened version
                    flat_num = self._num_members(flat_elem, accessor_name)
                    flat_names = self._member_names(flat_elem, accessor_name)
                    flat_members = self._members(flat_elem, accessor_name)
                    self.assertEqual(
                        flat_members,
                        self._accessor_members(flat_elem, accessor_name,
                                               names))
                    self.assertEqual(num, flat_num)
                    self.assertEqual(names, flat_names)
                    self.assertEqual(members, flat_members)
                    if class_name == 'Dynamics' and accessor_name in (
                            'alias', 'constant', 'state_variable', 'regime'):
                        if accessor_name == 'regime':
                            # All combination of sub-regimes
                            self.assertEqual(num, product(all_sc_nums))
                        else:
                            # Additional members representing local port
                            # connections and reduce ports are appended to list
                            # of certain members when flattening.
                            self.assertGreaterEqual(num, sum(all_sc_nums))
                    else:
                        self.assertEqual(num, sum(all_sc_nums))
                        self.assertEqual(names, sorted(all_sc_names))
                        self.assertEqual(
                            members,
                            sorted(all_sc_members, key=lambda e: e.key))

    @classmethod
    def _num_members(cls, elem, accessor_name):
        return getattr(elem, 'num_' + pluralise(accessor_name))

    @classmethod
    def _member_names(cls, elem, accessor_name):
        return sorted(getattr(elem, accessor_name + '_names'))

    @classmethod
    def _members(cls, elem, accessor_name):
        return sorted(getattr(elem, pluralise(accessor_name)),
                      key=lambda e: e.key)

    @classmethod
    def _accessor_members(cls, elem, accessor_name, names):
        accessor = getattr(elem, accessor_name)
        return [accessor(n) for n in names]


class TestRepr(unittest.TestCase):

    def test_repr(self):
        for name, elems in instances_of_all_types.iteritems():
            for elem in elems.itervalues():
                if name == 'NineMLDocument':
                    self.assertTrue(repr(elem).startswith('Document'))
                else:
                    self.assertTrue(
                        repr(elem).startswith(name),
                        "__repr__ for {} instance does not start with '{}' "
                        "('{}')"
                        .format(name, all_types[name].__name__, repr(elem)))
