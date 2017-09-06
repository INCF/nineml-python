import re
import unittest
from nineml.utils.testing.comprehensive import (
    all_types, instances_of_all_types)
from nineml.visitors.equality import MismatchFinder
import nineml.units as un
from nineml.abstraction import (
    Parameter, Constant, Dynamics, Regime,
    OutputEvent, StateVariable, On, AnalogSendPort,
    AnalogReceivePort, OnCondition, Trigger)


for nineml_type in all_types.itervalues():
    defining_attrs = set((a[1:] if a.startswith('_') else a)
                         for a in nineml_type.defining_attributes)
    nineml_attrs = set(
        nineml_type.nineml_attr + tuple(nineml_type.nineml_child.keys()) +
        tuple(c._children_iter_name() for c in nineml_type.nineml_children))
    if defining_attrs != nineml_attrs:
        missing = defining_attrs - nineml_attrs
        extra = nineml_attrs - defining_attrs
        print("{}, missing: {}, extra: {}".format(nineml_type.nineml_type,
                                                  missing, extra))


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
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current_voltage')] | [Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')]: 'm' attr of Dimension, [1] | [0]
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current_voltage')] | [Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')]: 'l' attr of Dimension, [2] | [0]
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current_voltage')] | [Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')]: 't' attr of Dimension, [-3] | [0]
[Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current_voltage')] | [Dynamics('dyn')>AnalogSendPort('A1')>Dimension('current')]: 'i' attr of Dimension, [0] | [1]
[Dynamics('dyn')] | [Dynamics('dyn')]: Parameter keys, ['P1', 'P2', 'P3', 'P4'] | ['P2', 'P3', 'P4']
[Dynamics('dyn')>Alias('A1')] | [Dynamics('dyn')>Alias('A1')]: 'rhs' attr of Alias, [P1*SV2] | [SV2]"""


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


b_mismatch = "[Dynamics('dyn')] | [Dynamics('dyn')]: AnalogSendPort keys, ['A1', 'A2'] | ['A1', 'A3']"


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


c_mismatch = "[Dynamics('dyn')>Alias('A4')] | [Dynamics('dyn')>Alias('A4')]: 'rhs' attr of Alias, [C2*SV1] | [2*C2*SV1]"


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
