import unittest
import logging
import sys
from tempfile import mkstemp
from nineml.base import (
    AnnotatedNineMLObject, DocumentLevelObject, ContainerObject)
from nineml.document import Document
from nineml.serialization import format_to_serializer, format_to_unserializer
from nineml.exceptions import name_error, NineMLSerializationNotSupportedError


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
        self._name = validate_identifier(name)
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
        self._name = validate_identifier(name)
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
        self._name = validate_identifier(name)
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


class C(AnnotatedNineMLObject, ContainerObject):

    nineml_type = 'C'
    nineml_attr = ('name', 't')
    nineml_child = {'f': F}
    nineml_children = (E,)

    def __init__(self, name, es, f, t):
        AnnotatedNineMLObject.__init__(self)
        ContainerObject.__init__(self)
        self.name = name
        self.add(*es)
        self.f = f
        self.t = t

    @name_error
    def e(self, name):
        return self._es[name]

    @property
    def es(self):
        return iter(self._es.values())

    @property
    def e_names(self):
        return iter(self._es.keys())

    @property
    def num_es(self):
        return len(self._es)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.children(self.es, reference=True)
        node.child(self.f, reference=False)
        node.attr('t', self.t)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   node.children(E, allow_ref=True),
                   node.child(F),
                   node.attr('t', dtype=float))


class G(AnnotatedNineMLObject):

    nineml_type = 'G'
    nineml_attr = ('value',)

    has_serial_body = 'only'

    def __init__(self, value):
        AnnotatedNineMLObject.__init__(self)
        self._value = value

    def __repr__(self):
        return 'G({})'.format(self.value)

    @property
    def value(self):
        return self._value

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.body(self.value, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.body(dtype=float, **options))


class H(AnnotatedNineMLObject):

    nineml_type = 'H'
    nineml_child = {'g': G}

    def __init__(self, g):
        self.g = g

    def __repr__(self):
        return 'H({})'.format(self.g)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.child(self.g, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.child(G))


class Container(ContainerObject, DocumentLevelObject):

    nineml_type = 'Container'
    nineml_type_v1 = 'Cunfaener'
    nineml_attr = ('name', 'bs', 'd')
    nineml_children = (B,)
    nineml_child = {'a': A,
                    'c': C,
                    'g': G}

    def __init__(self, name, a, bs, c, d, g):
        ContainerObject.__init__(self)
        self.name = name
        DocumentLevelObject.__init__(self)
        self.a = a
        self.add(*bs)
        self.c = c
        self.d = d
        self.g = g

    @property
    def num_bs(self):
        return (self._bs)

    @property
    def b_names(self):
        return iter(self._bs.keys())

    @name_error
    def b(self, name):
        return self._bs[name]

    @property
    def bs(self):
        return iter(self._bs.values())

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        node.child(self.a, reference=True)
        node.children(self.bs)
        node.child(self.c, within='CTag')
        node.attr('d', self.d)
        node.child(self.g)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('name'),
                   a=node.child(A, n=1, allow_ref=True),
                   bs=node.children(B, n='*'),
                   c=node.child(C, n=1, within='CTag'),
                   d=node.attr('d'),
                   g=node.child(G))


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
                t=4.7),
            d='wee',
            g=G(22.0))

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

    def test_flat_body(self):
        h = H(G(1.0))
        for format in format_to_serializer:  # @ReservedAssignment
            if format in h_strs:
                h_str = h.serialize(to_str=True, format=format, fname=None)
                new_h = H.unserialize(h_str, format, version=1.0)
                self.assertEqual(h, new_h)
                self.assertEqual(h_str, h_strs[format])


h_strs = {
    'xml': '<H xmlns="http://nineml.net/9ML/1.0"><G>1.0</G></H>',
    'yaml': 'H: {G: 1.0}\n',
    'json': '{"H": {"G": 1.0}}'}
