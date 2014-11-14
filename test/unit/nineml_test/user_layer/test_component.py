import os.path
import unittest
from nineml import read, load
from nineml.exceptions import NineMLUnitMismatchError

examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'neurons')


class TestComponent(unittest.TestCase):

    def test_component_xml_540degree_roundtrip(self):
        test_file = os.path.join(examples_dir, 'HodgkinHuxley.xml')
        context1 = read(test_file)
        xml = context1.to_xml()
        print xml.tostring(pretty_print=True)
        context2 = load(xml, read_from=test_file)
        self.assertEquals(context1, context2)

    def test_prototype_xml_540degree_roundtrip(self):
        test_file = os.path.join(examples_dir, 'HodgkinHuxleyModified.xml')
        context1 = read(test_file)
        xml = context1.to_xml()
        context2 = load(xml, read_from=test_file)
        self.assertEquals(context1, context2)

    def test_mismatch_dimension(self):
        context = read(os.path.join(examples_dir, 'HodgkinHuxleyBadUnits.xml'))
        with self.assertRaises(NineMLUnitMismatchError):
            context['HodgkinHuxleyBadUnits']
