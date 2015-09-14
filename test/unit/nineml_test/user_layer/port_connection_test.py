import os.path
import unittest
from nineml import Document
from nineml.user.port_connections import (AnalogPortConnection,
                                          EventPortConnection)


examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'neurons')


class TestPortConnection(unittest.TestCase):

    def test_xml_roundtrip(self):
        pc1 = AnalogPortConnection('response', 'destination', 'iSyn', 'iExt')
        document = Document()
        xml = pc1.to_xml(document)
        pc2 = AnalogPortConnection.from_xml(xml, document)
        self.assertEquals(pc1, pc2,
                          "XML round trip failed for AnalogPortConnection")
        pc1 = EventPortConnection('response', 'destination', 'iSyn', 'iExt')
        xml = pc1.to_xml(document)
        pc2 = EventPortConnection.from_xml(xml, document)
        self.assertEquals(pc1, pc2,
                          "XML round trip failed for AnalogPortConnection")
