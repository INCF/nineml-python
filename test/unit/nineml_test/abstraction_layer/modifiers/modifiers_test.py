import unittest
from copy import copy
from nineml.abstraction_layer.dynamics import (
    DynamicsClass, Regime, On, OutputEvent, StateAssignment, StateVariable,
    OnCondition, TimeDerivative)
from nineml.abstraction_layer import Alias, Parameter
from nineml.abstraction_layer.ports import AnalogSendPort, AnalogReceivePort


class Modifiers_test(unittest.TestCase):

    def setUp(self):

        self.a = DynamicsClass(
            name='A',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P2',
                    'dSV2/dt = SV1 / ARP1 + SV2 / P1',
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

        self.b = DynamicsClass(
            name='A',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1',
                     'A4 := SV1^3 + SV2^-3'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P2',
                    'dSV2/dt = SV1 / ARP1 + SV2 / P1',
                    'dSV3/dt = -SV3 + P3',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
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
                          AnalogSendPort('SV3')],
            parameters=['P1', 'P2', 'P3']
        )

    def test_add(self):
        # Copy templates
        a = copy(self.a)
        b = copy(self.b)
        # Add missing items
        a.add(Alias('A4', 'SV1^3 + SV2^-3'))
        a.add(StateVariable('SV3'))
        a.regime('R1').add(TimeDerivative('SV3', '-SV3 + P3'))
        a.regime('R2').add(OnCondition(
            'SV3 < 0.001', target_regime='R2',
            state_assignments=[StateAssignment('SV3', 1)]))
        a.add(Parameter('P3'))
        a.add(AnalogSendPort('SV3'))
        a.validate()
        self.assertEqual(b, a,
                         "Did not transform 'a' into 'b':\n {}"
                         .format(b.find_mismatch(a)))

    def test_remove(self):
        # Copy templates
        a = copy(self.a)
        b = copy(self.b)
        # Add missing items
        b.remove(b.alias('A4'))
        b.remove(b.state_variable('SV3'))
        b.regime('R1').remove(b.regime('R1').time_derivative('SV3'))
        b.regime('R2').remove(b.regime('R2').on_condition('SV3 < 0.001'))
        b.remove(b.analog_send_port('SV3'))
        b.remove(b.parameter('P3'))
        b.validate()
        self.assertEqual(a, b,
                         "Did not transform 'b' into 'a':\n {}"
                         .format(a.find_mismatch(b)))
        b.add(Alias('A5', 'P1 + P2'))
        self.assertNotEqual(a, b, "Added Alias was not detected")

    def test_contains(self):
        self.assertTrue(self.a.regime('R2') in self.a)
        self.assertFalse(self.a.regime('R2') in self.b)
        self.assertTrue(self.a.regime('R2').name in self.b)
        self.assertTrue(self.b.parameter('P3') in self.b)
        self.assertTrue('A1' in self.a)
