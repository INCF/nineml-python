import unittest
from nineml.annotations import Annotations
from nineml.xml import etree, nineml_ns


foreign_ns = "http://some.other.namespace.org"
unprocess_ns = "http://some.other.unprocessable.namespace.org"

annot_str = """
    <Annotations>
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
    </Annotations>""".format(foreign=foreign_ns, unprocess=unprocess_ns)

annot_xml = etree.parse(annot_str)


class TestAnnotations(unittest.TestCase):

    def test_annotations_load(self):

        annot_from_str = Annotations.from_xml(
            annot_xml, annotation_namespaces=[foreign_ns])
        annot = Annotations()
        annot[nineml_ns]['Bar']['a'] = '1'
        annot[foreign_ns]['Woo']['Car']['b'] = 1
        annot[foreign_ns]['Woo']['Jar']['c'] = 2
        annot[nineml_ns]['Boo']['Mar']['Wee']['d'] = 3
        annot[nineml_ns]['Boo']['Mar']['Wee']['e'] = 4
        annot[nineml_ns]['Boo']['Mar']['Waa']['f'] = 5
        annot[nineml_ns]['Boo']['Mar']['Waa']['g'] = 6
        self.assertEqual(annot[nineml_ns], annot_from_str[nineml_ns])
        self.assertEqual(annot[foreign_ns], annot_from_str[foreign_ns])
        self.assertIsInstance(annot[unprocess_ns], etree.Element)
