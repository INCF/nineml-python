import re
import unittest
from nineml.visitors.equality import MismatchFinder
import nineml.units as un
from nineml.abstraction import (
    Parameter, Constant, Dynamics, Regime,
    OutputEvent, StateVariable, On, AnalogSendPort,
    AnalogReceivePort, OnCondition, Trigger)


class TestFindMismatch(unittest.TestCase):

    def test_find_mismatch(self):
        finder = MismatchFinder()
        self.assertEqual(self._strip(finder.find(ref, A)),
                         self._strip(a_mismatch),
                         '\nGenerated\n---\n{}\n\nReference\n---\n{}'
                         .format(finder.find(ref, A), a_mismatch))
        self.assertEqual(self._strip(finder.find(ref, B)),
                         self._strip(b_mismatch),
                         '\nGenerated\n---\n{}\n\nReference\n---\n{}'
                         .format(finder.find(ref, B), b_mismatch))
        self.assertEqual(self._strip(finder.find(ref, C)),
                         self._strip(c_mismatch),
                         '\nGenerated\n---\n{}\n\nReference\n---\n{}'
                         .format(finder.find(ref, C), c_mismatch))
        self.assertEqual(self._strip(finder.find(ref, D)),
                         self._strip(d_mismatch),
                         '\nGenerated\n---\n{}\n\nReference\n---\n{}'
                         .format(finder.find(ref, D), d_mismatch))
        finder_ns = MismatchFinder(annotations_ns=['NS1'])
        self.assertEqual(self._strip(finder_ns.find(ref, E)),
                         self._strip(e_mismatch),
                         '\nGenerated\n---\n{}\n\nReference\n---\n{}'
                         .format(finder_ns.find(ref, E), e_mismatch))
        self.assertEqual(self._strip(finder_ns.find(ref, F)),
                         self._strip(f_mismatch),
                         '\nGenerated\n---\n{}\n\nReference\n---\n{}'
                         .format(finder_ns.find(ref, G), f_mismatch))
        self.assertEqual(self._strip(finder.find(ref, G)),
                         self._strip(g_mismatch),
                         '\nGenerated\n---\n{}\n\nReference\n---\n{}'
                         .format(finder.find(ref, G), g_mismatch))

    @classmethod
    def _strip(cls, string):
        return re.sub(r'\s+', ' ', string).strip()


ref = Dynamics(
    name='dyn',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1',
                                 dimension=un.voltage * un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])

ref.state_variable('SV2').annotations.set(('Z1', 'NS1'), 'Y1', 'X1', 2.0)

A = Dynamics(
    name='dyn',
    aliases=['A1:=SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1', dimension=un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])


a_mismatch = """
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')] - 'm' attr: [1] | [0]
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')] - 'l' attr: [2] | [0]
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')] - 't' attr: [-3] | [0]
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')] - 'i' attr: [0] | [1]
[Dynamics('dyn')] - Parameter keys: ['P1', 'P2', 'P3', 'P4'] | ['P2', 'P3', 'P4']
[Dynamics('dyn')>Alias('A1')] - 'rhs' attr: [P1*SV2] | [SV2]
"""

B = Dynamics(
    name='dyn',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1',
                                 dimension=un.voltage * un.current),
                  AnalogSendPort('A3', dimension=un.voltage)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])


b_mismatch = """
[Dynamics('dyn')] - AnalogSendPort keys: ['A1', 'A2'] | ['A1', 'A3']
"""


C = Dynamics(
    name='dyn',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := 2*C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1',
                                 dimension=un.voltage * un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])


c_mismatch = """
[Dynamics('dyn')>Alias('A4')] - 'rhs' attr: [C2*SV1] | [2*C2*SV1]
"""


D = Dynamics(
    name='dyn',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1',
                                 dimension=un.voltage * un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])

d_mismatch = ""


E = Dynamics(
    name='dyn',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1',
                                 dimension=un.voltage * un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])

E.state_variable('SV2').annotations.set(('Z1', 'NS1'), 'Y1', 'X1', 3.0)

e_mismatch = """
[Dynamics('dyn')] - 'NS1' annotations: [[{NS1}Z1:{NS1}Y1:X1=2.0]] | [[{NS1}Z1:{NS1}Y1:X1=3.0]]
"""


F = Dynamics(
    name='dyn',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1',
                                 dimension=un.voltage * un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])

F.state_variable('SV2').annotations.set(('Z1', 'NS1'), 'Y1', 'X1', 2.0)

f_mismatch = ""


G = Dynamics(
    name='dyn',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'),
                            do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1',
                                 dimension=un.voltage * un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=-72.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])

g_mismatch = """
[Dynamics('dyn')>Constant('C1')] - 'value' attr: [-71.0] | [-72.0]
"""
