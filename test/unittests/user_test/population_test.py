import os.path
import unittest
from nineml import read, load
from nineml.exceptions import NineMLXMLBlockError, NineMLXMLAttributeError


class TestPopulation(unittest.TestCase):

    test_file1 = os.path.join(os.path.dirname(__file__), '..', '..',
                              'xml', 'populations', 'simple.xml')

    test_file2 = os.path.join(os.path.dirname(__file__), '..', '..',
                              'xml', 'populations', 'bad_xml')

    def test_xml_540degree_roundtrip(self):
        document1 = read(self.test_file1)
        xml = document1.to_xml()
        document2 = load(xml, read_from=self.test_file)
        self.assertEquals(document1, document2,
                          "Documents don't match after write/read from file:\n"
                          "{}".format(document2.find_mismatch(document1)))

    def test_unprocessed_block(self):
        doc = read(self.test_file2)
        self.assertRaises(NineMLXMLBlockError,
                          doc.__getitem__,
                          'BadBlock')
        self.assertRaises(NineMLXMLAttributeError,
                          doc.__getitem__,
                          'BadAttribute')
