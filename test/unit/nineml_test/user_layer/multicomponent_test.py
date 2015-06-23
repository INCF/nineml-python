import os.path
import unittest
from nineml import load, Document
from nineml.user.multicomponent import (
    MultiComponent, SubComponent, PortExposure, MultiCompartment,
    FromSibling, FromDistal, FromProximal, Branches, Mapping,
    Domain)
from nineml.user.port_connections import PortConnection
from nineml.user.component import DynamicsProperties


examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'neurons')


class TestComponent(unittest.TestCase):

    def test_multicomponent_xml_roundtrip(self):
        comp1 = MultiComponent(
            name='test',
            subcomponents=[SubComponent(DynamicsProperties())],
            port_exposures=[])
        xml = Document(comp1).to_xml()
        comp2 = load(xml)['test']
        self.assertEquals(comp1, comp2)

    def test_multicompartment_xml_roundtrip(self):
        comp1 = MultiCompartment(
            name='test',
            mapping=Mapping(),
            branches=Branches(),
            domains=[Domain(DynamicsProperties())])
        xml = Document(comp1).to_xml()
        comp2 = load(xml)['test']
        self.assertEquals(comp1, comp2)
