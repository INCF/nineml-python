import unittest
from nineml.annotations import Annotations
from nineml.xml import etree, nineml_ns, ElementMaker


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
            <Bar>invalid in simple annotations format</Bar>
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

    def test_annotations_load(self):

        loaded_annot = Annotations.from_xml(
            annot_xml, annotation_namespaces=[foreign_ns])
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
