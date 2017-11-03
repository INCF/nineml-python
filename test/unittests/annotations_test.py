import unittest
from copy import deepcopy
from nineml.annotations import Annotations, PY9ML_NS
from nineml.abstraction import Parameter, Dynamics, Alias
from nineml.units import Dimension
from nineml import Document
from nineml.utils import xml_equal
import nineml.units as un
from nineml.serialization import DEFAULT_VERSION, NINEML_NS
from lxml import etree
from nineml.serialization.xml import ElementMaker
import logging
import sys

logger = logging.getLogger('NineML')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


foreign_ns = "http://some.other.namespace.org"
another_ns = "http://another.namespace.org"

E = ElementMaker(namespace=NINEML_NS,
                 nsmap={None: NINEML_NS})
another_E = ElementMaker(namespace=another_ns)


annot_str = """
<Annotations xmlns="{nineml}">
    <Foo xmlns="{py9ml}">
      <Bar a="1" xmlns="{py9ml}"/>
    </Foo>
    <Woo xmlns="{foreign}">
      <Car b="1" xmlns="{foreign}"/>
      <Jar c="2" xmlns="{foreign}"/>
    </Woo>
    <Foo xmlns="{another}">
      <Bar xmlns="{another}">annotations with text fields</Bar>
    </Foo>
    <Boo xmlns="{py9ml}">
      <Mar xmlns="{py9ml}">
        <Wee d="3" e="4" xmlns="{py9ml}"/>
        <Waa f="5" g="6" xmlns="{py9ml}"/>
      </Mar>
    </Boo>
  </Annotations>""".format(nineml=NINEML_NS, py9ml=PY9ML_NS,
                             foreign=foreign_ns, another=another_ns)

annot_xml = etree.fromstring(annot_str)


class TestAnnotations(unittest.TestCase):

    version = 1

    def setUp(self):
        self.annot = Annotations.unserialize(annot_xml, 'xml', DEFAULT_VERSION)

    def test_basic(self):
        annot = Annotations()
        annot.set(('Foo', PY9ML_NS), 'Bar', 'a', '1')
        annot.set(('Woo', foreign_ns), 'Car', 'b', 1)
        annot.set(('Woo', foreign_ns), 'Jar', 'c', 2)
        annot.add(('Foo', another_ns), 'Bar')
        annot[('Foo',
               another_ns)][0]['Bar'][0]._body = 'annotations with text fields'
        annot.set(('Boo', PY9ML_NS), 'Mar', 'Wee', 'd', 3)
        annot.set(('Boo', PY9ML_NS), 'Mar', 'Wee', 'e', 4)
        annot.set(('Boo', PY9ML_NS), 'Mar', 'Waa', 'f', 5)
        annot.set(('Boo', PY9ML_NS), 'Mar', 'Waa', 'g', 6)
        self.assertEqual(annot, self.annot,
                         "Manual annotations do not match loaded "
                         "annotations:\n\n{}\nvs\n\n{}\n\nMismatch:\n{}"
                         .format(annot, self.annot,
                                 annot.find_mismatch(self.annot)))
        reloaded_annot = Annotations.unserialize(annot_xml, 'xml',
                                                 DEFAULT_VERSION)
        self.assertEqual(self.annot, reloaded_annot)

    def test_read_annotations_and_annotate_xml(self):
        param_xml = E(Parameter.nineml_type,
                      deepcopy(annot_xml), name="P1",
                      dimension="dimensionless")
        dim_xml = E(Dimension.nineml_type,
                     deepcopy(annot_xml), name='dimensionless')
        doc = Document()
        dimension = Dimension.unserialize(
            dim_xml, format='xml', version=DEFAULT_VERSION, document=doc)
        doc.add(dimension)
        parameter = Parameter.unserialize(
            param_xml, format='xml', version=DEFAULT_VERSION, document=doc)
        self.assertEqual(parameter.annotations, self.annot,
                         "{}\n\nvs\n\n{}".format(parameter.annotations,
                                                 self.annot))
        self.assertEqual(dimension.annotations, self.annot,
                         "{}\n\nvs\n\n{}".format(dimension.annotations,
                                                 self.annot))
        re_param_xml = parameter.serialize(
            format='xml', version=DEFAULT_VERSION, document=doc)
        re_dim_xml = dimension.serialize(format='xml', version=DEFAULT_VERSION,
                                         document=doc)
        self.assertTrue(xml_equal(param_xml, re_param_xml, annotations=True),
                        "\n{}\n does not equal\n\n{}".format(
                            etree.tostring(param_xml, pretty_print=True),
                            etree.tostring(re_param_xml, pretty_print=True)))
        self.assertTrue(xml_equal(dim_xml, re_dim_xml, annotations=True),
                        "\n{}\n does not equal\n\n{}".format(
                            etree.tostring(dim_xml, pretty_print=True),
                            etree.tostring(re_dim_xml, pretty_print=True)))

    def test_get_set(self):
        annot = Annotations()
        annot.set(('a', 'dummy_ns'), 'b', 'c', 'd', 1.5)
        self.assertEqual(
            annot.get(('a', 'dummy_ns'), 'b', 'c', 'd'), '1.5')
        self.assertRaises(
            KeyError, annot.get, ('a', 'dummy_ns'), 'b', 'c', 'e')
        self.assertEqual(
            annot.get(('a', 'dummy_ns'), 'b', 'c', 'e', default=2.0), 2.0)
        self.assertRaises(
            KeyError, annot.get, ('a', 'wummy_ns'), 'b', 'c', 'd')
        self.assertEqual(
            annot.get(('a', 'wummy_ns'), 'b', 'c', 'd', default=3.0), 3.0)
        annot.set(('a', 'dummy_ns'), 'b', 'x', 4.0)
        annot.set(('a', 'dummy_ns'), 'b', 'y', 5.0)
        annot.set(('a', 'dummy_ns'), 'b', 'z', 6.0)
        self.assertEqual(annot.get(('a', 'dummy_ns'), 'b', 'x'), '4.0')
        branch = annot[('a', 'dummy_ns')][0]['b'][0]
        self.assertEqual(sorted(branch.attr_keys()), ['x', 'y', 'z'])
        self.assertEqual(sorted(branch.attr_values()), ['4.0', '5.0', '6.0'])
        self.assertEqual(sorted(branch.attr_items()), [('x', '4.0'),
                                                       ('y', '5.0'),
                                                       ('z', '6.0')])

    def test_delete(self):
        annot = Annotations()
        annot.set(('a', 'ns'), 'b', 'c', 'd', 'e', 1)
        self.assertFalse(annot.empty())
        self.assertEqual(annot.get(('a', 'ns'), 'b', 'c', 'd', 'e'), '1')
        annot.delete(('a', 'ns'), 'b', 'c', 'd', 'e')
        self.assertTrue(annot.empty())

    def test_equals_with_annotations_ns(self):
        a = Dynamics(
            name='D',
            parameters=[Parameter('P', dimension=un.dimensionless)],
            aliases=[Alias('A', 'P')])
        b = a.clone()
        c = a.clone()
        d = a.clone()
        e = a.clone()
        a.parameter('P').annotations.set(('annot1', 'dummy_ns'), 'val1', 1.0)
        b.parameter('P').annotations.set(('annot1', 'dummy_ns'), 'val1', 1.0)
        c.parameter('P').annotations.set(('annot1', 'dummy_ns'), 'val1', 2.0)
        e.parameter('P').annotations.set(('annot1', 'dummy_ns2'), 'val1', 1.0)
        self.assertTrue(a.equals(b, annotations_ns=['dummy_ns']))
        self.assertTrue(a.equals(c))
        self.assertFalse(a.equals(c, annotations_ns=['dummy_ns']))
        self.assertTrue(a.equals(d))
        self.assertFalse(a.equals(d, annotations_ns=['dummy_ns']))
        self.assertTrue(a.equals(e))
        self.assertFalse(a.equals(e, annotations_ns=['dummy_ns']))
