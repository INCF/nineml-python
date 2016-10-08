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

    def test_assign_roles(self):
        role2name = {
            'pre': 'pre_cell', 'post': 'post_cell', 'response': 'psr',
            'plasticity': 'pls'}
        epc = EventPortConnection(
            send_port='ESP1',
            receive_port='ERP1',
            sender_role='pre',
            receiver_role='plasticity')
        apc = AnalogPortConnection(
            send_port='SV1',
            receive_port='ARP1',
            sender_role='response',
            receiver_role='post')
        internal_epc = epc.assign_names_from_roles(role2name)
        self.assertEqual(internal_epc.send_port_name, 'ESP1')
        self.assertEqual(internal_epc.receive_port_name, 'ERP1')
        self.assertEqual(internal_epc.sender_name, 'pre_cell')
        self.assertEqual(internal_epc.receiver_name, 'pls')
        external_epc = epc.append_namespace_from_roles(role2name)
        self.assertEqual(external_epc.send_port_name, 'ESP1__pre_cell')
        self.assertEqual(external_epc.receive_port_name, 'ERP1__pls')
        internal_apc = apc.assign_names_from_roles(role2name)
        self.assertEqual(internal_apc.send_port_name, 'SV1')
        self.assertEqual(internal_apc.receive_port_name, 'ARP1')
        self.assertEqual(internal_apc.sender_name, 'psr')
        self.assertEqual(internal_apc.receiver_name, 'post_cell')
        external_apc = apc.append_namespace_from_roles(role2name)
        self.assertEqual(external_apc.send_port_name, 'SV1__psr')
        self.assertEqual(external_apc.receive_port_name, 'ARP1__post_cell')
