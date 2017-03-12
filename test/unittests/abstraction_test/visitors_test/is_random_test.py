import unittest
from nineml.abstraction.dynamics import (
    Dynamics, Regime, On, OutputEvent)
from nineml.abstraction import Alias
from nineml.abstraction.ports import AnalogSendPort, AnalogReceivePort


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsRequiredDefinitions_test(unittest.TestCase):

    def setUp(self):

        self.a = Dynamics(
            name='A',
            aliases=['A1:=P1', 'A2 := ARP2', 'A3 := SV1'],
            regimes=[
                Regime('dSV1/dt = -SV1 / (P2*t)',
                       'dSV2/dt = A2/t + A3/t + ARP1/t',
                       name='R1',
                       transitions=On('input', 'SV1 = SV1 + 1'))],
            analog_ports=[AnalogReceivePort('ARP1'),
                          AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'),
                          AnalogSendPort('A2')],
            parameters=['P1', 'P2']
        )

        self.b = Dynamics(
            name='B',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / (P2*t)',
                    'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    aliases=[Alias('A1', 'P1 * 2')],
                    name='R1',
                ),
                Regime(name='R2', transitions=On(
                    'SV1 > 1', 'SV1 = SV1 * random.normal()', to='R1'))
            ],
            analog_ports=[AnalogReceivePort('ARP1'), AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'), AnalogSendPort('A2')],
            parameters=['P1', 'P2']
        )

    def test_is_random(self):
        self.assertFalse(self.a.is_random)
        self.assertTrue(self.b.is_random)
