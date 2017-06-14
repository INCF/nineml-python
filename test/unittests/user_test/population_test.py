import os.path
import unittest
from nineml import read
from nineml.serialization.xml import XMLUnserializer
from nineml.serialization import DEFAULT_VERSION


class TestPopulation(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), '..', '..',
                              'xml', 'populations', 'simple.xml')

    def test_xml_540degree_roundtrip(self):
        document1 = read(self.test_file)
        xml = document1.serialize(version=DEFAULT_VERSION)
        document2 = XMLUnserializer(xml, url=self.test_file,
                                    version=DEFAULT_VERSION).unserialize()
        self.assertEquals(document1, document2,
                          "Documents don't match after write/read from file:\n"
                          "{}".format(document2.find_mismatch(document1)))
