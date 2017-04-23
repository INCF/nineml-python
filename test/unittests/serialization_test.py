import unittest
from nineml.base import BaseNineMLObject
# from nineml.serialization.json import (
#     Unserializer as Ujson, Serializer as Sjson)
# from nineml.serialization.yaml import (
#     Unserializer as Uyaml, Serializer as Syaml)
# from nineml.serialization.hdf5 import (
#     Unserializer as Uhdf5, Serializer as Shdf5)
# from nineml.serialization.pickle import (
#     Unserializer as Upkl, Serializer as Spkl)
from nineml.serialization.xml import (
    Unserializer as Uxml, Serializer as Sxml)


class Container(BaseNineMLObject):

    nineml_type = 'Container'
    defining_attributes = ('a', 'bs', 'c', 'd')

    def __init__(self, a, bs, c, d):
        self.a = a
        self.bs = bs
        self.c = c
        self.d = d

    def serialize(self, elem):
        elem.child(self._a)
        elem.children(self._bs)
        elem.child(self._c, within='CTag')
        elem.attr('d', self._d)

    @classmethod
    def unserialize(cls, elem):
        return cls(a=elem.child(A, n=1),
                   bs=elem.children(B, n='*'),
                   c=elem.child(C, n=1, within='CTag'),
                   d=elem.attr('d'))


class A(BaseNineMLObject):

    nineml_type = 'A'
    defining_attributes = ('a1', 'a2')

    def __init__(self, a1, a2):
        self.a1 = a1
        self.a2 = a2

    def serialize(self, elem):  # @UnusedVariable
        elem.attr('a1', self.a1)
        elem.attr('a2', self.a2)

    @classmethod
    def unserialize(cls, elem):  # @UnusedVariable
        return cls(elem.attr('a1'), elem.attr('a2'))


class B(BaseNineMLObject):

    nineml_type = 'B'
    defining_attributes = ('b',)

    def __init__(self, b):
        self.b = b

    def serialize(self, elem):  # @UnusedVariable
        elem.attr('b', self.b)

    @classmethod
    def unserialize(cls, elem):  # @UnusedVariable
        return cls(elem.attr('b'))


class C(BaseNineMLObject):

    nineml_type = 'C'
    defining_attributes = ('c1', 'c2')

    def __init__(self, c1, c2):
        self._c1 = c1
        self._c2 = c2

    def serialize(self, elem):  # @UnusedVariable
        elem.attr('c1', self._c1)
        elem.attr('c2', self._c2)

    @classmethod
    def unserialize(cls, elem, U, **options):  # @UnusedVariable
        return cls(elem.attr('c1'), elem.attr('c2'))


class TestSerialization(unittest.TestCase):

    def setUp(self):
        self.container = Container(
            a=A(1, 2), b=B('b'), c=C(1, 2), d='d')

    def test_rountrip(self):
        for U, S in (
            # (Ujson, Sjson),
            # (Uyaml, Syaml),
            # (Uhdf5, Shdf5),
            # (Upkl, Spkl),
                (Uxml, Sxml),):
            elem = self.container.serialize(S)
            new_container = Container.unserialize(elem, U)
            self.assertEqual(self.container, new_container,
                             self.container.find_mismatch(new_container))
