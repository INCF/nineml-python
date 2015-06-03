import unittest
from copy import copy
from nineml.abstraction.dynamics import (
    Dynamics, Regime, On, OutputEvent, StateAssignment, StateVariable,
    OnCondition, TimeDerivative)
from nineml.abstraction import Alias, Parameter
from nineml.abstraction.ports import AnalogSendPort, AnalogReceivePort
from nineml.exceptions import NineMLInvalidElementTypeException


class MemberContainer_test(unittest.TestCase):

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
            name='A',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1',
                     'A4 := SV1^3 + SV2^-3'],
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
        a.regime('R1').add(TimeDerivative('SV3', '-SV3/t + P3/t'))
        a.regime('R1').on_event('spikein').add(StateAssignment('SV1', 'P1'))
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
        b.regime('R1').on_event('spikein').remove(
            b.regime('R1').on_event('spikein').state_assignment('SV1'))
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
        self.assertTrue(self.b.regime('R2').on_condition('SV3 < 0.001')
                        .state_assignment('SV3') in self.b)

    def test_getitem(self):
        self.assertIs(self.a.alias('A1'), self.a['A1'])
        self.assertIs(self.a.parameter('P2'), self.a['P2'])
        self.assertIs(self.b.state_variable('SV2'), self.b['SV2'])
        self.assertIsNot(self.a.state_variable('SV2'), self.b['SV2'])
        self.assertIsNot(self.a.analog_send_port('A1'), self.a['A1'])
        self.assertIs(self.b.regime('R2'), self.b['R2'])
        self.assertIs(self.b['R1'].time_derivative('SV3'), self.b['R1']['SV3'])

    def test_indexof(self):
        self.assertEqual(self.a.index_of(self.a['A1']),
                         self.a.index_of(self.a['A1']))
        self.assertNotEqual(self.a.index_of(self.a['A1']),
                            self.a.index_of(self.a['A2']))
        r1 = self.a.regime('R1')
        self.assertEqual(r1.index_of(r1.time_derivative('SV2')),
                         r1.index_of(r1.time_derivative('SV2')))
        sa = (self.b.regime('R2').on_condition('SV3 < 0.001')
              .state_assignment('SV3'))
        self.assertEqual(self.b.index_of(sa, key='StateAssignments'),
                         self.b.index_of(sa, key='StateAssignments'))
        self.assertRaises(NineMLInvalidElementTypeException,
                          self.b.index_of, sa)
