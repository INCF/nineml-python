from __future__ import division
import unittest
from nineml.abstraction_layer import (
    Parameter, Constant, DynamicsClass, Regime, On, OutputEvent, StateVariable,
    StateAssignment)
from nineml.abstraction_layer.ports import AnalogSendPort, AnalogReceivePort
from nineml import units as un
from nineml.exceptions import NineMLRuntimeError


class Dimensionality_test(unittest.TestCase):

    def test_good_model(self):

        DynamicsClass(
            name='A',
            aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            state_variables=[
                StateVariable('SV1', dimension=un.voltage),
                StateVariable('SV2', dimension=un.current)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P2',
                    'dSV2/dt = A3 / ARP2 + SV2 / P2',
                    transitions=[On('SV1 > P3', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1'
                ),
                Regime(name='R2', transitions=On('SV1 > C1', to='R1'))
            ],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                          AnalogReceivePort('ARP2',
                                            dimension=(un.resistance *
                                                       un.time)),
                          AnalogSendPort('A1',
                                         dimension=un.voltage * un.current),
                          AnalogSendPort('A2', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.time),
                        Parameter('P3', dimension=un.voltage)],
            constants=[Constant('C1', value=1.0, units=un.mV)]
        )

    def test_internally_inconsistent(self):

        self.assertRaises(
            NineMLRuntimeError,
            DynamicsClass,
            name='A',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = SV1 + P1',
                    name='R1'
                ),
            ],
            parameters=[Parameter('P1', dimension=un.time)],
        )
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsClass,
            name='A',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = SV1/t',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')])],
                    name='R1'
                ),
            ],
            parameters=[Parameter('P1', dimension=un.time)],
        )
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsClass,
            name='A',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = SV1/t',
                    transitions=[On('SV1 > P1',
                                    do=[StateAssignment('SV1', 'SV1 + RP1')])],
                    name='R1'
                ),
            ],
            parameters=[Parameter('P1', dimension=un.voltage)],
            analog_ports=[AnalogReceivePort('RP1', dimension=un.time)],
        )

    def test_mismatch_with_declared(self):

        self.assertRaises(
            NineMLRuntimeError,
            DynamicsClass,
            name='A',
            state_variables=[StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = SV1/t',
                    name='R1'
                ),
            ],
            analog_ports=[AnalogSendPort('SV1', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.voltage)],
        )
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsClass,
            name='A',
            state_variables=[StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = SV1 * P1',
                    name='R1'
                ),
            ],
            parameters=[Parameter('P1', dimension=un.time)],
        )
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsClass,
            name='A',
            state_variables=[StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = SV1/t',
                    transitions=[On('SV1 > P1',
                                    do=[StateAssignment('SV1', 'P2')])],
                    name='R1'
                ),
            ],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.time)],
        )
