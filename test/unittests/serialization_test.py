import unittest
from nineml.base import (
    AnnotatedNineMLObject, DocumentLevelObject, ContainerObject)
from nineml.document import Document
# from nineml.serialization.json import (
#     Unserialize_noder as Ujson, Serializer as Sjson)
# from nineml.serialization.yaml import (
#     Unserialize_noder as Uyaml, Serializer as Syaml)
# from nineml.serialization.hdf5 import (
#     Unserialize_noder as Uhdf5, Serializer as Shdf5)
# from nineml.serialization.pickle import (
#     Unserialize_noder as Upkl, Serializer as Spkl)
from nineml.serialization.xml import (
    Unserializer as Uxml, Serializer as Sxml)
from lxml import etree

F_ANNOT_NS = 'http:/a.domain.org'
F_ANNOT_TAG = 'FAnnotation'
F_ANNOT_ATTR = 'f_annot'
F_ANNOT_VAL = 'annot_f'


class Container(AnnotatedNineMLObject, DocumentLevelObject):

    nineml_type = 'Container'
    v1_nineml_type = 'Cunfaener'
    defining_attributes = ('name', 'a', 'bs', 'c', 'd')

    def __init__(self, name, a, bs, c, d, document=None):
        AnnotatedNineMLObject.__init__(self)
        self.name = name
        DocumentLevelObject.__init__(self, document)
        self.a = a
        self.bs = bs
        self.c = c
        self.d = d

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.child(self.a, reference=True)
        node.children(self.bs)
        node.child(self.c, within='CTag')
        node.attr('d', self.d)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   a=node.child(A, n=1, allow_ref=True),
                   bs=node.children(B, n='*'),
                   c=node.child(C, n=1, within='CTag'),
                   d=node.attr('d'))


class A(AnnotatedNineMLObject, DocumentLevelObject):

    nineml_type = 'A'
    defining_attributes = ('name', 'a1', 'a2')
    default_a1 = 5

    def __init__(self, name, a1, a2, document=None):
        AnnotatedNineMLObject.__init__(self)
        self.name = name
        DocumentLevelObject.__init__(self, document)
        self.a1 = a1
        self.a2 = a2

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        if node.later_version('2.0', equal=True):
            node.attr('a1', self.a1)
        node.attr('a2', self.a2)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        if node.later_version(2.0, equal=True):
            a1 = node.attr('a1', dtype=int)
        else:
            a1 = cls.default_a1
        return cls(node.attr('name'),
                   a1,
                   node.attr('a2', dtype=float))


class B(AnnotatedNineMLObject):

    nineml_type = 'B'
    defining_attributes = ('name', 'b',)

    def __init__(self, name, b):
        super(B, self).__init__()
        self.name = name
        self.b = b

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('b', self.b)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('b'))


class C(AnnotatedNineMLObject, ContainerObject):

    nineml_type = 'C'
    defining_attributes = ('name', 'es', 'f')
    class_to_member = {'E': 'e'}

    def __init__(self, name, es, f, g):
        super(C, self).__init__()
        self.name = name
        self._es = dict((e.name, e) for e in es)
        self.f = f
        self.g = g

    def e(self, name):
        return self._es[name]

    @property
    def es(self):
        return self._es.itervalues()

    @property
    def e_names(self):
        return self._es.iterkeys()

    @property
    def num_es(self):
        return len(self._es)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.children(self.es, reference=True)
        node.child(self.f, reference=True)
        node.attr('g', self.g)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.children(E, allow_ref=True),
                   node.child(F, allow_ref=True),
                   node.attr('g', dtype=float))


class E(AnnotatedNineMLObject, DocumentLevelObject):

    nineml_type = 'E'
    defining_attributes = ('name', 'e1', 'e2')

    def __init__(self, name, e1, e2, document=None):
        AnnotatedNineMLObject.__init__(self)
        self.name = name
        DocumentLevelObject.__init__(self, document)
        self.name = name
        self.e1 = e1
        self.e2 = e2

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('e1', self.e1)
        node.attr('e2', self.e2)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('e1', dtype=int),
                   node.attr('e2', dtype=int))


class F(AnnotatedNineMLObject, DocumentLevelObject):

    nineml_type = 'F'
    defining_attributes = ('name', 'f1', 'f2')

    def __init__(self, name, f1, f2, document=None):
        AnnotatedNineMLObject.__init__(self)
        self.name = name
        DocumentLevelObject.__init__(self, document)
        self.name = name
        self.f1 = f1
        self.f2 = f2

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('f1', self.f1)
        node.attr('f2', self.f2)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('f1', dtype=int),
                   node.attr('f2', dtype=int))


class TestSerialization(unittest.TestCase):

    def test_rountrip(self):
        for version in (1, 2):
            for U, S in (
                # (Ujson, Sjson),
                # (Uyaml, Syaml),
                # (Uhdf5, Shdf5),
                # (Upkl, Spkl),
                    (Uxml, Sxml),):
                doc = Document()
                f = F('F', 10, 20)
                f.annotations.set((F_ANNOT_TAG, F_ANNOT_NS), F_ANNOT_ATTR,
                                  F_ANNOT_VAL)
                a = A('A', A.default_a1, 2.5)
                container = Container(
                    name='a_container',
                    a=a,
                    bs=[
                        B('B', 'x'),
                        B('B', 'y')],
                    c=C(name='C',
                        es=[E('E1', 1, 2),
                            E('E2', 3, 4),
                            E('E3', 5, 6)],
                        f=f,
                        g=4.7),
                    d='d')
                doc.add(container, clone=False)
                serializer = S(document=doc, version=version)
                container_elem = serializer.visit(container)
                print etree.tostring(serializer.root_elem(), pretty_print=True)
                new_container = U(document=doc, version=version).visit(
                    container_elem, Container)
                self.assertTrue(container.equals(new_container,
                                                 annot_ns=[F_ANNOT_NS]),
                                container.find_mismatch(new_container))
