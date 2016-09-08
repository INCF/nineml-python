import unittest
from nineml.utils.testing.comprehensive import (
    all_types, instances_of_all_types)


class TestAccessors(unittest.TestCase):

    pass


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
