import unittest
from nineml.utils.testing.comprehensive import (
    all_types, instances_of_all_types)


class TestAccessors(unittest.TestCase):

    def test_accessors(self):
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
                for member in cls.class_to_member:
                    for elem in instances_of_all_types[name]:
                        num = elem._num_members(member, cls.class_to_member)
                        names = list(elem._member_names_iter(
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
                            "('{}')".format(member, elem._name, name,
                                            names))
                        self.assertEqual(
                            len(names), len(set(names)),
                            "Duplicate names found in {} members of '{}' {} "
                            "('{}')".format(member, elem._name, name, names))
                        # Check all members are of the correct type
                        self.assertTrue(
                            all(m.nineml_type == member for m in members),
                            "Not all {} members accessed in '{}' {} via "
                            "iterator were of {} type ({})"
                            .format(member, elem._name, name, member,
                                    ', '.join(str(m) for m in members)))
                        self.assertEqual(
                            members, accessor_members,
                            "{} members accessed through iterator ({}) do not "
                            "match members accessed through individual "
                            "accessor method ({}) for '{}' {}"
                            .format(member, members, accessor_members,
                                    elem._name, name))


class TestRepr(unittest.TestCase):

    def test_repr(self):
        for name, elems in instances_of_all_types.iteritems():
            for elem in elems:
                if name == 'NineMLDocument':
                    self.assertTrue(repr(elem).startswith('Document'))
                else:
                    self.assertTrue(
                        repr(elem).startswith(name),
                        "__repr__ for {} instance does not start with '{}' ('{}')"
                        .format(name, all_types[name].__name__, repr(elem)))
