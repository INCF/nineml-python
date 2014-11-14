import os.path
import unittest
from nineml import read, load
from lxml import etree


class TestPopulation(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'populations', 'simple.xml')

    def test_xml_540degree_roundtrip(self):
        context1 = read(self.test_file)
        xml = context1.to_xml()
        print etree.tostring(xml, pretty_print=True)
        context2 = load(xml, read_from=self.test_file)
        self.assertEquals(context1, context2)
