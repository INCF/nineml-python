import os.path
import unittest
from nineml import read
from nineml.exceptions import NineMLXMLBlockError, NineMLXMLAttributeError


class TestPopulation(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), '..', 'xml',
                             'bad_xml.xml')

    def setUp(self):
        self.doc = read(self.test_file)

    def test_bad_block(self):
        self.assertRaises(NineMLXMLBlockError,
                          self.doc.__getitem__,
                          'BadBlock')

    def test_bad_attribute(self):
        self.assertRaises(NineMLXMLAttributeError,
                          self.doc.__getitem__,
                          'BadAttribute1')
        self.assertRaises(NineMLXMLAttributeError,
                          self.doc.__getitem__,
                          'BadAttribute2')

    def test_missing_attribute(self):
        self.assertRaises(NineMLXMLAttributeError,
                          self.doc.__getitem__,
                          'MissingAttribute')

    def test_missing_block(self):
        self.assertRaises(NineMLXMLBlockError,
                          self.doc.__getitem__,
                          'MissingBlock1')
        self.assertRaises(NineMLXMLBlockError,
                          self.doc.__getitem__,
                          'MissingBlock2')
