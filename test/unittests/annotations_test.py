import unittest
from copy import deepcopy
from nineml.annotations import Annotations
from nineml.xml import etree, nineml_ns, ElementMaker, E
from nineml.abstraction import Parameter
from nineml.units import Dimension
from nineml.abstraction.dynamics.visitors.xml import (
    DynamicsXMLLoader, DynamicsXMLWriter)
from nineml import Document
from nineml.utils import xml_equal


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

    def test_basic(self):

        loaded_annot = Annotations.from_xml(
            annot_xml, read_annotation_ns=[foreign_ns])
        annot = Annotations()
        annot[nineml_ns]['Foo']['Bar']['a'] = '1'
        annot[foreign_ns]['Woo']['Car']['b'] = 1
        annot[foreign_ns]['Woo']['Jar']['c'] = 2
        annot[nineml_ns]['Boo']['Mar']['Wee']['d'] = 3
        annot[nineml_ns]['Boo']['Mar']['Wee']['e'] = 4
        annot[nineml_ns]['Boo']['Mar']['Waa']['f'] = 5
        annot[nineml_ns]['Boo']['Mar']['Waa']['g'] = 6
        self.assertEqual(annot[nineml_ns], loaded_annot[nineml_ns],
                         "Manual annotations do not match loaded "
                         "annotations:\n\n{}\nvs\n\n{}\n".format(
                             annot[nineml_ns], loaded_annot[nineml_ns]))
        self.assertEqual(annot[foreign_ns], loaded_annot[foreign_ns])
        self.assertIsInstance(loaded_annot[unprocess_ns], etree._Element)
        reloaded_annot = Annotations.from_xml(
            annot_xml, read_annotation_ns=foreign_ns)
        self.assertEqual(loaded_annot, reloaded_annot)

    def test_read_annotations_and_annotate_xml(self):
        param_xml = E(Parameter.nineml_type,
                      deepcopy(annot_xml), name="P1",
                      dimension="dimensionless")
        dim_xml = E(Dimension.nineml_type,
                     deepcopy(annot_xml), name='dimensionless')
        annot = Annotations.from_xml(
            annot_xml, read_annotation_ns=foreign_ns)
        doc = Document()
        dimension = Dimension.from_xml(dim_xml, doc,
                                       read_annotation_ns=foreign_ns)
        doc.add(dimension)
        loader = DynamicsXMLLoader(doc)
        parameter = loader.load_parameter(param_xml,
                                          read_annotation_ns=foreign_ns)
        self.assertEqual(parameter.annotations, annot,
                         "{}\n\nvs\n\n{}".format(parameter.annotations, annot))
        self.assertEqual(dimension.annotations, annot,
                         "{}\n\nvs\n\n{}".format(dimension.annotations, annot))
        writer = DynamicsXMLWriter(doc, E)
        re_param_xml = writer.visit_parameter(parameter)
        re_dim_xml = dimension.to_xml(doc)
        self.assertTrue(xml_equal(param_xml, re_param_xml))
        self.assertTrue(xml_equal(dim_xml, re_dim_xml))
