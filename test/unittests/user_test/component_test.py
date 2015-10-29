import os.path
import unittest
from nineml import read, Document
from nineml.exceptions import NineMLRuntimeError
from nineml.user import Property
from nineml import Unit, Dimension

voltage = Dimension('voltage', m=1, l=2, t=-3, i=-1)
mV = Unit(name='mV', dimension=voltage, power=-3)

examples_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                            'xml', 'neurons')


class TestComponent(unittest.TestCase):

    def test_component_xml_540degree_roundtrip(self):
        test_file = os.path.join(examples_dir, 'HodgkinHuxley.xml')
        document1 = read(test_file)
        xml = document1.to_xml()
        document2 = Document.load(xml, url=test_file)
        if document1 != document2:
            mismatch = document1.find_mismatch(document2)
        else:
            mismatch = ''
        self.assertEquals(document1, document2, mismatch)

    def test_prototype_xml_540degree_roundtrip(self):
        test_file = os.path.join(examples_dir, 'HodgkinHuxleyModified.xml')
        document1 = read(test_file)
        xml = document1.to_xml()
        document2 = Document.load(xml, url=test_file)
        if document1 != document2:
            mismatch = document1.find_mismatch(document2)
        else:
            mismatch = ''
        self.assertEquals(document1, document2, mismatch)

    def test_mismatch_dimension(self):
        document = read(os.path.join(examples_dir,
                                     'HodgkinHuxleyBadUnits.xml'))
        with self.assertRaises(NineMLRuntimeError):
            document['HodgkinHuxleyBadUnits']


class PropertyTest(unittest.TestCase):

    def test_xml_roundtrip(self):
        document = Document()
        p1 = Property("tau_m", 20.0 * mV)
        element = p1.to_xml(document)
        p2 = Property.from_xml(element, Document(mV))
        self.assertEqual(p1, p2)
