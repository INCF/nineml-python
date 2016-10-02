import re
import unittest
import nineml.units as un
from nineml.abstraction import (
    Parameter, Constant, Dynamics, Regime,
    OutputEvent, StateVariable, On, AnalogSendPort,
    AnalogReceivePort, OnCondition, Trigger)

ws_re = re.compile(r'\s')


class TestFindMismatch(unittest.TestCase):

    Aref = """
        Attribute '_parameters': keys do not match:
            self:'P1', 'P2', 'P3', 'P4'
            other:'P2', 'P3', 'P4'
        Attribute '_aliases':
            Key 'A1':
              Attribute 'rhs': mismatch in type self:Mul != other:Symbol
        Attribute '_analog_send_ports':
            Key 'A1':
              Attribute 'dimension':
                  Attribute '_dims': self:(1, 2, -3, 0, 0, 0, 0) != other:(0, 0, 0, 1, 0, 0, 0)
        """

    Bref = """
            Attribute '_analog_send_ports': keys do not match:
              self:'A1', 'A2'
              other:'A1', 'A3'
            """

    Cref = """"""

    Dref = """
            Attribute '_aliases':
                Key 'A4':
                  Attribute 'rhs': self:C2*SV1 != other:2*C2*SV1
            """

    def test_find_difference(self):
        dyn = Dynamics(
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
                                       target_regime='R1')])
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
                                       target_regime='R1')])
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
                                       target_regime='R1')])
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
        C = Dynamics(
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
                                       target_regime='R1')])
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
        D = Dynamics(
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
                                       target_regime='R1')])
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
        self.assertEqual(self._strip(dyn.find_mismatch(A)),
                         self._strip(self.Aref),
                         '\nGenerated\n---\n{}\n\nReference\n----{}'
                         .format(dyn.find_mismatch(A), self.Aref))
        self.assertEqual(self._strip(dyn.find_mismatch(B)),
                         self._strip(self.Bref),
                         '\nGenerated\n---\n{}\n\nReference\n----{}'
                         .format(dyn.find_mismatch(B), self.Bref))
        self.assertEqual(self._strip(dyn.find_mismatch(C)),
                         self._strip(self.Cref),
                         '\nGenerated\n---\n{}\n\nReference\n----{}'
                         .format(dyn.find_mismatch(C), self.Cref))
        self.assertEqual(self._strip(dyn.find_mismatch(D)),
                         self._strip(self.Dref),
                         '\nGenerated\n---\n{}\n\nReference\n----{}'
                         .format(dyn.find_mismatch(D), self.Dref))

    @classmethod
    def _strip(cls, string):
        return re.sub(r'\s+', ' ', string).strip()
