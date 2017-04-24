import unittest
from nineml.base import BaseNineMLObject
from nineml.document import Document
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

    def serialize(self, node, **options):  # @UnusedVariable
        node.child(self._a)
        node.children(self._bs)
        node.child(self._c, within='CTag')
        node.attr('d', self._d)

    @classmethod
    def unserialize(cls, node, **options):  # @UnusedVariable
        return cls(a=node.child(A, n=1),
                   bs=node.children(B, n='*'),
                   c=node.child(C, n=1, within='CTag'),
                   d=node.attr('d'))


class A(BaseNineMLObject):

    nineml_type = 'A'
    defining_attributes = ('a1', 'a2')

    def __init__(self, a1, a2):
        self.a1 = a1
        self.a2 = a2

    def serialize(self, node, **options):  # @UnusedVariable
        node.attr('a1', self.a1)
        node.attr('a2', self.a2)

    @classmethod
    def unserialize(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('a1'), node.attr('a2'))


class B(BaseNineMLObject):

    nineml_type = 'B'
    defining_attributes = ('b',)

    def __init__(self, b):
        self.b = b

    def serialize(self, node, **options):  # @UnusedVariable
        node.attr('b', self.b)

    @classmethod
    def unserialize(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('b'))


class C(BaseNineMLObject):

    nineml_type = 'C'
    defining_attributes = ('c1', 'c2')

    def __init__(self, c1, c2):
        self._c1 = c1
        self._c2 = c2

    def serialize(self, node, **options):  # @UnusedVariable
        node.attr('c1', self._c1)
        node.attr('c2', self._c2)

    @classmethod
    def unserialize(cls, node, U, **options):  # @UnusedVariable
        return cls(node.attr('c1'), node.attr('c2'))


class TestSerialization(unittest.TestCase):

    def test_rountrip(self):
        container = Container(
            a=A(1, 2), b=B('b'), c=C(1, 2), d='d')
        for version in (1, 2):
            for U, S in (
                # (Ujson, Sjson),
                # (Uyaml, Syaml),
                # (Uhdf5, Shdf5),
                # (Upkl, Spkl),
                    (Uxml, Sxml),):
                doc = Document()
                elem = S(document=doc, version=version).visit(container)
                new_container = U(document=doc, version=version).visit(
                    elem, Container)
                self.assertEqual(container, new_container,
                                 container.find_mismatch(new_container))
