"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import types


class UnequalException(Exception):

    def __init__(self, o1, o2, msg=""):
        Exception.__init__(self)
        self.msg = msg
        self.o1 = o1
        self.o2 = o2

    def __str__(self):
        s = self.msg
        s += '\nO1: %s' % str(self.o1)
        s += '\nO2: %s' % str(self.o2)
        return s


def assert_equal(o1, o2, msg=''):
    if not isinstance(o1, (types.NoneType, basestring)):
        print o1, o2
        assert not (o1 is o2)
    assert type(o1) == type(o2)
    assert isinstance(o1, (basestring, types.NoneType))
    if o1 == o2:
        return
    raise UnequalException(o1, o2, msg)


def assert_equal_list(o1, o2, msg='', do_sort=True):
    assert o1 is not o2
    assert type(o1) == type(o2)
    assert isinstance(o1, (tuple, list))
    if do_sort and sorted(o1) == sorted(o2):
        return
    raise UnequalException(sorted(o1), sorted(o2), msg)


class ComponentEqualityChecker(object):

    @classmethod
    def check_equal(cls, comp1, comp2, strict_aliases=True):
        """Forwarding Function :Easier Interface"""
        cls.check_equal_component(comp1, comp2, strict_aliases=strict_aliases)
