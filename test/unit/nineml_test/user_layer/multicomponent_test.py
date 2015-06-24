import os.path
import unittest
from nineml import load, Document
from nineml.user.multicomponent import (
    MultiComponent, SubComponent, PortExposure, MultiCompartment,
    FromSibling, FromDistal, FromProximal, Mapping, Domain)
from nineml.abstraction import (
    Dynamics, Regime, AnalogReceivePort, OutputEvent, AnalogSendPort, On,
    StateAssignment)
from nineml.user.port_connections import PortConnection
from nineml.user.component import DynamicsProperties


examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'neurons')


class TestMultiComponent(unittest.TestCase):

    def setUp(self): 

        self.a = Dynamics(
            name='A',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / (P2*t)',
                    'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1',
                ),
                Regime(name='R2', transitions=On('SV1 > 1', to='R1'))
            ],
            analog_ports=[AnalogReceivePort('ARP1'),
                          AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'), AnalogSendPort('A2')],
            parameters=['P1', 'P2']
        )

        self.b = Dynamics(
            name='B',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1',
                     'A4 := SV1^3 + SV2^3'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / (P2*t)',
                    'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
                    'dSV3/dt = -SV3/t + P3/t',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[
                                    OutputEvent('emit'),
                                    StateAssignment('SV1', 'P1')])],
                    name='R1',
                ),
                Regime(name='R2', transitions=[
                    On('SV1 > 1', to='R1'),
                    On('SV3 < 0.001', to='R2',
                       do=[StateAssignment('SV3', 1)])])
            ],
            analog_ports=[AnalogReceivePort('ARP1'),
                          AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'),
                          AnalogSendPort('A2'),
                          AnalogSendPort('A3'),
                          AnalogSendPort('SV3')],
            parameters=['P1', 'P2', 'P3']
        )

        self.a_props = DynamicsProperties(
            name="AProps", definition=self.a, properties={'P1': 1, 'P2': 2})
        self.b_props = DynamicsProperties(
            name="BProps", definition=self.b, properties={'P1': 1, 'P2': 2,
                                                          'P3': 3})

    def test_multicomponent_xml_roundtrip(self):
        comp1 = MultiComponent(
            name='test',
            subcomponents=[
                SubComponent(
                    name='a',
                    dynamics=self.a_props,
                    port_connections=[
                        PortConnection('ARP1', FromSibling('A1', 'b')),
                        PortConnection('ARP2', FromSibling('A2', 'b'))]),
                SubComponent(
                    name='b',
                    dynamics=self.b_props,
                    port_connections=[
                        PortConnection('ARP1', FromSibling('A1', 'a')),
                        PortConnection('ARP3', FromSibling('A3', 'a'))])],
            port_exposures=[
                PortExposure(
                    name="b_ARP2",
                    component="b",
                    port="ARP2")])
        xml = Document(comp1, self.a, self.b).to_xml()
        comp2 = load(xml)['test']
        self.assertEquals(comp1, comp2)

    def test_multicompartment_xml_roundtrip(self):
        comp1 = MultiCompartment(
            name='test',
            tree=Tree(
                ArrayValue([0, 1, 2, 3, 2, 3])),
            mapping=Mapping([0, 0, 0, 1, 1, 1]),
            domains=[
                Domain(
                    index=0,
                    dynamics=self.a_props,
                    port_connections=[
                        PortConnection('ARP1', FromDistal('A1')),
                        PortConnection('ARP2', FromProximal('A2')),
                        PortConnection('ARP3',
                                       FromDistal('A3', domain='dendrites'))]),
                Domain(
                    index=1,
                    dynamics=self.b_props,
                    port_connections=[
                        PortConnection('ARP1', FromDistal('A1')),
                        PortConnection('ARP2', FromProximal('A2'))])])
        xml = Document(comp1, self.a, self.b).to_xml()
        comp2 = load(xml)['test']
        self.assertEquals(comp1, comp2)
