import os.path
import unittest
from nineml import read, load


class TestPopulation(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                             '..', '..', 'examples', 'xml', 'populations',
                             'simple.xml')

    def test_xml_540degree_roundtrip(self):
        context1 = read(self.test_file)
        xml = context1.to_xml()
        context2 = load(xml, read_from=self.test_file)
        self.assertEquals(context1, context2)
