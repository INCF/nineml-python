import unittest
import logging
import sys
import pickle
from tempfile import mkstemp
from nineml.base import (
    AnnotatedNineMLObject, DocumentLevelObject, ContainerObject)
from nineml.document import Document
from nineml.serialization import format_to_serializer, format_to_unserializer


F_ANNOT_NS = 'http:/a.domain.org'
F_ANNOT_TAG = 'AnAnnotationTag'
F_ANNOT_ATTR = 'an_annotation_attr_name'
F_ANNOT_VAL = 'an_annotation_value'


logger = logging.getLogger('NineML')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class A(AnnotatedNineMLObject, DocumentLevelObject):

    nineml_type = 'A'
    nineml_attr = ('name', 'x', 'y')
    default_x = 5

    def __init__(self, name, x, y):
        AnnotatedNineMLObject.__init__(self)
        self._name = name
        DocumentLevelObject.__init__(self)
        self.x = x
        self.y = y

    @property
    def name(self):
        return self._name

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('x', self.x)
        node.attr('y', self.y)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        x = node.attr('x', dtype=int)
        return cls(node.attr('name'),
                   x,
                   node.attr('y', dtype=float))

    def serialize_node_v1(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('y', self.y)

    @classmethod
    def unserialize_node_v1(cls, node, **options):  # @UnusedVariable
        x = cls.default_x
        return cls(node.attr('name'),
                   x,
                   node.attr('y', dtype=float))


class B(AnnotatedNineMLObject):

    nineml_type = 'B'
    nineml_attr = ('name', 'z',)

    def __init__(self, name, z):
        super(B, self).__init__()
        self._name = name
        self.z = z

    @property
    def name(self):
        return self._name

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('z', self.z)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('z'))


class E(AnnotatedNineMLObject, DocumentLevelObject):

    nineml_type = 'E'
    nineml_attr = ('name', 'u', 'v')

    def __init__(self, name, u, v):
        AnnotatedNineMLObject.__init__(self)
        self._name = name
        DocumentLevelObject.__init__(self)
        self.u = u
        self.v = v

    @property
    def name(self):
        return self._name

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('u', self.u)
        node.attr('v', self.v)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('u', dtype=int),
                   node.attr('v', dtype=int))


class C(AnnotatedNineMLObject, ContainerObject):

    nineml_type = 'C'
    nineml_attr = ('name', 'f', 'g')
    nineml_children = (E,)

    def __init__(self, name, es, f, g):
        AnnotatedNineMLObject.__init__(self)
        ContainerObject.__init__(self)
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
        node.child(self.f, reference=False)
        node.attr('g', self.g)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.children(E, allow_ref=True),
                   node.child(F),
                   node.attr('g', dtype=float))


class F(AnnotatedNineMLObject, DocumentLevelObject):

    nineml_type = 'F'
    nineml_attr = ('name', 'w', 'r')

    def __init__(self, name, w, r):
        AnnotatedNineMLObject.__init__(self)
        self.name = name
        DocumentLevelObject.__init__(self)
        self.name = name
        self.w = w
        self.r = r

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.attr('w', self.w)
        node.attr('r', self.r)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.attr('w', dtype=int),
                   node.attr('r', dtype=int))


class Container(ContainerObject, DocumentLevelObject):

    nineml_type = 'Container'
    nineml_type_v1 = 'Cunfaener'
    nineml_attr = ('name', 'bs', 'd')
    nineml_children = (B,)
    nineml_child = {'a': A,
                    'c': C}

    def __init__(self, name, a, bs, c, d):
        ContainerObject.__init__(self)
        self.name = name
        DocumentLevelObject.__init__(self)
        self.a = a
        self._bs = dict((b.name, b) for b in bs)
        self.c = c
        self.d = d

    @property
    def num_bs(self):
        return (self._bs)

    @property
    def b_names(self):
        return self._bs.iterkeys()

    def b(self, name):
        self._bs[name]

    @property
    def bs(self):
        return self._bs.itervalues()

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


class_map = {'Container': Container,
             'Cunfaener': Container, 'A': A, 'E': E, 'F': F}


class TestSerialization(unittest.TestCase):

    def setUp(self):
        f = F('an_F', 10, 20)
        f.annotations.set((F_ANNOT_TAG, F_ANNOT_NS), F_ANNOT_ATTR,
                          F_ANNOT_VAL)
        a = A('an_A', A.default_x, 2.5)
        self.container = Container(
            name='a_container',
            a=a,
            bs=[
                B('a_B', 'foo'),
                B('another_B', 'bar')],
            c=C(name='a_C',
                es=[E('an_E', 1, 2),
                    E('another_E', 3, 4),
                    E('yet_another_E', 5, 6)],
                f=f,
                g=4.7),
            d='wee')

    def test_roundtrip(self):
        for version in (2, 1):
            for format in format_to_serializer:  # @ReservedAssignment @IgnorePep8
                S = format_to_serializer[format]
                U = format_to_unserializer[format]
                if S is None or U is None:
                    logger.warning(
                        "Skipping over '{}' serialization test as it required "
                        "modules were note imported"
                        .format(format))
                doc = Document(self.container)
                # Make temp file for serializers that write directly to file
                # (e.g. HDF5)
                _, fname = mkstemp()
                serial_doc = S(document=doc, version=version,
                               fname=fname).serialize()
                new_doc = U(root=serial_doc, version=version,
                            class_map=class_map).unserialize()
                self.assertTrue(new_doc.equals(doc, annot_ns=[F_ANNOT_NS]),
                                new_doc.find_mismatch(doc))

    def test_to_str(self):
        for format in ('json', 'yaml', 'xml'):  # @ReservedAssignment
            for version in (2, 1):
                # Check serialization to string
                a = self.container.a
                serial_str = a.serialize(to_str=True, format=format,
                                         version=version)
                new_a = A.unserialize(
                    serial_str, format=format, version=version)
                self.assertTrue(new_a.equals(a, annot_ns=[F_ANNOT_NS]),
                                new_a.find_mismatch(a))
