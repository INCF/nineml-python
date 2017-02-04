import unittest
from copy import deepcopy
from nineml.annotations import Annotations
from nineml.xml import etree, nineml_ns, ElementMaker, E
from nineml.abstraction import Parameter, Dynamics, Alias
from nineml.units import Dimension
from nineml.abstraction.dynamics.visitors.xml import (
    DynamicsXMLLoader, DynamicsXMLWriter)
from nineml import Document
from nineml.utils import xml_equal
from nineml.exceptions import NineMLRuntimeError
import nineml.units as un


foreign_ns = "http://some.other.namespace.org"
unprocess_ns = "http://some.other.unprocessable.namespace.org"

unp_E = ElementMaker(namespace=unprocess_ns, nsmap={None: unprocess_ns})

annot_str = """
    <Annotations xmlns="{nineml}">
        <Foo>
            <Bar a="1"/>
        </Foo>
        <Woo xmlns="{foreign}">
            <Car b="1"/>
            <Jar c="2"/>
        </Woo>
        <Foo xmlns="{unprocess}">
            <Bar>invalid in simple annotations format so just kept as XML</Bar>
        </Foo>
        <Boo>
            <Mar>
                <Wee d="3" e="4"/>
                <Waa f="5" g="6"/>
            </Mar>
        </Boo>
    </Annotations>""".format(nineml=nineml_ns,
                             foreign=foreign_ns, unprocess=unprocess_ns)

annot_xml = etree.fromstring(annot_str)


class TestAnnotations(unittest.TestCase):

    def setUp(self):
        self.annot = Annotations.from_xml(
            annot_xml, annotations_ns=[foreign_ns])

    def test_basic(self):
        annot = Annotations()
        annot.set(nineml_ns, 'Foo', 'Bar', 'a', '1')
        annot.set(foreign_ns, 'Woo', 'Car', 'b', 1)
        annot.set(foreign_ns, 'Woo', 'Jar', 'c', 2)
        annot.set(nineml_ns, 'Boo', 'Mar', 'Wee', 'd', 3)
        annot.set(nineml_ns, 'Boo', 'Mar', 'Wee', 'e', 4)
        annot.set(nineml_ns, 'Boo', 'Mar', 'Waa', 'f', 5)
        annot.set(nineml_ns, 'Boo', 'Mar', 'Waa', 'g', 6)
        self.assertEqual(annot[nineml_ns], self.annot[nineml_ns],
                         "Manual annotations do not match loaded "
                         "annotations:\n\n{}\nvs\n\n{}\n".format(
                             annot[nineml_ns], self.annot[nineml_ns]))
        self.assertEqual(annot[foreign_ns], self.annot[foreign_ns])
        self.assertIsInstance(self.annot[unprocess_ns], etree._Element)
        reloaded_annot = Annotations.from_xml(
            annot_xml, annotations_ns=foreign_ns)
        self.assertEqual(self.annot, reloaded_annot)

    def test_read_annotations_and_annotate_xml(self):
        param_xml = E(Parameter.nineml_type,
                      deepcopy(annot_xml), name="P1",
                      dimension="dimensionless")
        dim_xml = E(Dimension.nineml_type,
                     deepcopy(annot_xml), name='dimensionless')
        doc = Document()
        dimension = Dimension.from_xml(dim_xml, doc,
                                       annotations_ns=foreign_ns)
        doc.add(dimension)
        loader = DynamicsXMLLoader(doc)
        parameter = loader.load_parameter(param_xml,
                                          annotations_ns=foreign_ns)
        self.assertEqual(parameter.annotations, self.annot,
                         "{}\n\nvs\n\n{}".format(parameter.annotations,
                                                 self.annot))
        self.assertEqual(dimension.annotations, self.annot,
                         "{}\n\nvs\n\n{}".format(dimension.annotations,
                                                 self.annot))
        writer = DynamicsXMLWriter(doc, E)
        re_param_xml = writer.visit_parameter(parameter)
        re_dim_xml = dimension.to_xml(doc)
        self.assertTrue(xml_equal(param_xml, re_param_xml))
        self.assertTrue(xml_equal(dim_xml, re_dim_xml))

    def test_get_set(self):
        annot = Annotations()
        annot.set('dummy_ns', 'a', 'b', 'c', 'd', 1.5)
        self.assertEqual(
            annot.get('dummy_ns', 'a', 'b', 'c', 'd'), '1.5')
        self.assertRaises(
            KeyError, annot.get, 'dummy_ns', 'a', 'b', 'c', 'e')
        self.assertEqual(
            annot.get('dummy_ns', 'a', 'b', 'c', 'e', default=2.0), 2.0)
        self.assertRaises(
            KeyError, annot.get, 'wummy_ns', 'a', 'b', 'c', 'd')
        self.assertEqual(
            annot.get('wummy_ns', 'a', 'b', 'c', 'd', default=3.0), 3.0)
        self.assertRaises(NineMLRuntimeError,
                          annot['dummy_ns'].__setitem__,
                          'another_ns', {})
        branch = annot['dummy_ns']['a']['b']
        branch.set('x', 4.0)
        branch.set('y', 5.0)
        branch.set('z', 6.0)
        self.assertEqual(branch.get('x'), '4.0')
        self.assertEqual(sorted(branch), ['x', 'y', 'z'])
        self.assertEqual(sorted(branch.keys()), ['x', 'y', 'z'])
        self.assertEqual(sorted(branch.values()), ['4.0', '5.0', '6.0'])
        self.assertEqual(sorted(branch.items()), [('x', '4.0'),
                                                  ('y', '5.0'),
                                                  ('z', '6.0')])

    def test_equals_with_annotations_ns(self):
        a = Dynamics(
            name='D',
            parameters=[Parameter('P', dimension=un.dimensionless)],
            aliases=[Alias('A', 'P')])
        b = a.clone()
        c = a.clone()
        d = a.clone()
        e = a.clone()
        a.parameter('P').annotations.set('dummy_ns', 'annot1', 'val1', 1.0)
        b.parameter('P').annotations.set('dummy_ns', 'annot1', 'val1', 1.0)
        c.parameter('P').annotations.set('dummy_ns', 'annot1', 'val1', 2.0)
        e.parameter('P').annotations.set('dummy_ns2', 'annot1', 'val1', 1.0)
        self.assertTrue(a.equals(b, annotations_ns=['dummy_ns']))
        self.assertTrue(a.equals(c))
        self.assertFalse(a.equals(c, annotations_ns=['dummy_ns']))
        self.assertTrue(a.equals(d))
        self.assertFalse(a.equals(d, annotations_ns=['dummy_ns']))
        self.assertTrue(a.equals(e))
        self.assertFalse(a.equals(e, annotations_ns=['dummy_ns']))
