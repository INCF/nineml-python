import unittest
from nineml.abstraction_layer import (
    Parameter, Constant, DynamicsClass, Regime, On, OutputEvent, StateVariable)
from nineml.abstraction_layer.ports import AnalogSendPort, AnalogReceivePort
from nineml import units as un


class Dimensionality_test(unittest.TestCase):

    def test_after_cloning(self):

        DynamicsClass(
            name='A',
            aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            state_variables=[
                StateVariable('SV1', dimension=un.voltage),
                StateVariable('SV2', dimension=un.current)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P1',
                    'dSV2/dt = A3 / ARP2 + SV2 / P2',
                    transitions=[On('SV1 > P3', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1'
                ),
                Regime(name='R2', transitions=On('SV1 > C1', to='R1'))
            ],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                          AnalogReceivePort('ARP2', dimension=un.resistance),
                          AnalogSendPort('A1',
                                         dimension=un.voltage * un.current),
                          AnalogSendPort('A2', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.time),
                        Parameter('P3', dimension=un.voltage)],
            constants=[Constant('C1', value=1.0, units=un.mV)]
        )
