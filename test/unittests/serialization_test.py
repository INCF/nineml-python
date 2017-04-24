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
from lxml import etree


class Container(BaseNineMLObject):

    nineml_type = 'Container'
    v1_nineml_type = 'Cunfaener'
    defining_attributes = ('a', 'bs', 'c', 'd')

    def __init__(self, name, a, bs, c, d):
        self._name = name
        self.a = a
        self.bs = bs
        self.c = c
        self.d = d

    def serialize(self, node, **options):  # @UnusedVariable
        node.attr('name', self._name)
        node.child(self.a)
        node.children(self.bs)
        node.child(self.c, within='CTag')
        node.attr('d', self.d)

    @classmethod
    def unserialize(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   a=node.child(A, n=1),
                   bs=node.children(B, n='*'),
                   c=node.child(C, n=1, within='CTag'),
                   d=node.attr('d'))


class A(BaseNineMLObject):

    nineml_type = 'A'
    defining_attributes = ('a1', 'a2')
    default_a1 = 5

    def __init__(self, name, a1, a2):
        self._name = name
        self.a1 = a1
        self.a2 = a2

    def serialize(self, node, **options):  # @UnusedVariable
        node.attr('name', self._name)
        if node.later_version('2.0', equal=True):
            node.attr('a1', self.a1)
        node.attr('a2', self.a2)

    @classmethod
    def unserialize(cls, node, **options):  # @UnusedVariable
        if node.later_version(2.0, equal=True):
            a1 = node.attr('a1', dtype=int)
        else:
            a1 = cls.default_a1
        return cls(node.attr('name'),
                   a1,
                   node.attr('a2', dtype=float))


class B(BaseNineMLObject):

    nineml_type = 'B'
    defining_attributes = ('b',)

    def __init__(self, name, b):
        self._name = name
        self.b = b

    def serialize(self, node, **options):  # @UnusedVariable
        node.attr('name', self._name)
        node.attr('b', self.b)

    @classmethod
    def unserialize(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('b'))


class C(BaseNineMLObject):

    nineml_type = 'C'
    defining_attributes = ('c1', 'c2')

    def __init__(self, name, c1, c2):
        self._name = name
        self.c1 = c1
        self.c2 = c2

    def serialize(self, node, **options):  # @UnusedVariable
        node.attr('name', self._name)
        node.attr('c1', self.c1)
        node.attr('c2', self.c2)

    @classmethod
    def unserialize(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('c1', dtype=int),
                   node.attr('c2', dtype=int))


class TestSerialization(unittest.TestCase):

    def test_rountrip(self):
        container = Container(
            name='a_container', a=A('a', A.default_a1, 2.5), bs=[B('b', 'B')],
            c=C('c', 1, 2), d='d')
        for version in (1, 2):
            for U, S in (
                # (Ujson, Sjson),
                # (Uyaml, Syaml),
                # (Uhdf5, Shdf5),
                # (Upkl, Spkl),
                    (Uxml, Sxml),):
                doc = Document()
                elem = S(document=doc, version=version).visit(container)
                print etree.tostring(elem, pretty_print=True)
                new_container = U(document=doc, version=version).visit(
                    elem, Container)
                self.assertEqual(container, new_container,
                                 container.find_mismatch(new_container))
