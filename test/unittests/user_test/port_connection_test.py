import os.path
import unittest
from nineml import Document
from nineml.user.port_connections import (AnalogPortConnection,
                                          EventPortConnection)
from nineml.utils.testing.comprehensive import projD


examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'neurons')


class TestPortConnection(unittest.TestCase):

    def test_xml_roundtrip(self):
        pc1 = AnalogPortConnection('response', 'destination', 'iSyn', 'iExt')
        document = Document()
        xml = pc1.serialize(format='xml', version=2, document=document)
        pc2 = AnalogPortConnection.unserialize(xml, format='xml', version=2, document=document)
        self.assertEquals(pc1, pc2,
                          "XML round trip failed for AnalogPortConnection")
        pc1 = EventPortConnection('response', 'destination', 'iSyn', 'iExt')
        xml = pc1.serialize(format='xml', version=2, document=document)
        pc2 = EventPortConnection.unserialize(xml, format='xml', version=2, document=document)
        self.assertEquals(pc1, pc2,
                          "XML round trip failed for AnalogPortConnection")

    def test_assign_from_roles(self):
        role2name = {
            'pre': 'pre_cell', 'post': 'post_cell', 'response': 'psr',
            'plasticity': 'pls'}
        epc = EventPortConnection(
            send_port_name='ESP1',
            receive_port_name='ERP1',
            sender_role='pre',
            receiver_role='response')
        apc = AnalogPortConnection(
            send_port_name='SV1',
            receive_port_name='ARP1',
            sender_role='response',
            receiver_role='post')
        # Test the creation of a new port connection with the original
        # port connection roles mapped to names of sub-components
        internal_epc = epc.assign_names_from_roles(role2name)
        self.assertEqual(internal_epc.send_port_name, 'ESP1')
        self.assertEqual(internal_epc.receive_port_name, 'ERP1')
        self.assertEqual(internal_epc.sender_name, 'pre_cell')
        self.assertEqual(internal_epc.receiver_name, 'psr')
        internal_apc = apc.assign_names_from_roles(role2name)
        self.assertEqual(internal_apc.send_port_name, 'SV1')
        self.assertEqual(internal_apc.receive_port_name, 'ARP1')
        self.assertEqual(internal_apc.sender_name, 'psr')
        self.assertEqual(internal_apc.receiver_name, 'post_cell')
        # Test the appending of role names to port_connection ports for
        # use in the creation of multi-dynamics
        external_epc = epc.append_namespace_from_roles(role2name)
        self.assertEqual(external_epc.send_port_name, 'ESP1__pre_cell')
        self.assertEqual(external_epc.receive_port_name, 'ERP1__psr')
        external_apc = apc.append_namespace_from_roles(role2name)
        self.assertEqual(external_apc.send_port_name, 'SV1__psr')
        self.assertEqual(external_apc.receive_port_name, 'ARP1__post_cell')
        # Bind the port connections to the projection "container" and then
        # call expose_ports to create port exposures for each of the
        # terminals
        epc.bind(projD, to_roles=True)
        epc_send_exp, epc_receive_exp = epc.expose_ports(role2name)
        self.assertEqual(epc_send_exp.name, 'ESP1__pre_cell')
        self.assertEqual(epc_send_exp.sub_component_name, 'pre_cell')
        self.assertEqual(epc_send_exp.port_name, 'ESP1')
        self.assertEqual(epc_receive_exp.name, 'ERP1__psr')
        self.assertEqual(epc_receive_exp.sub_component_name, 'psr')
        self.assertEqual(epc_receive_exp.port_name, 'ERP1')
        apc.bind(projD, to_roles=True)
        apc_send_exp, apc_receive_exp = apc.expose_ports(role2name)
        self.assertEqual(apc_send_exp.name, 'SV1__psr')
        self.assertEqual(apc_send_exp.sub_component_name, 'psr')
        self.assertEqual(apc_send_exp.port_name, 'SV1')
        self.assertEqual(apc_receive_exp.name, 'ARP1__post_cell')
        self.assertEqual(apc_receive_exp.sub_component_name, 'post_cell')
        self.assertEqual(apc_receive_exp.port_name, 'ARP1')

