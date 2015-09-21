import unittest
from nineml.abstraction.dynamics import (
    Dynamics, Regime, On, OutputEvent)
from nineml.abstraction.ports import AnalogSendPort, AnalogReceivePort


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsRenameSymbols_test(unittest.TestCase):

    def test_rename_symbol(self):

        a = Dynamics(
            name='A',
            aliases=['A1_a:=P1_a', 'A2_a := ARP1_a + SV2_a', 'A3_a := SV1_a'],
            regimes=[
                Regime(
                    'dSV1_a/dt = -SV1_a / (P2_a*t)',
                    'dSV2_a/dt = SV1_a / (ARP1_a*t) + SV2_a / (P1_a*t)',
                    transitions=[On('SV1_a > P1_a', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1_a',
                ),
                Regime(name='R2_a', transitions=On('SV1_a > 1', to='R1_a'))
            ],
            analog_ports=[AnalogReceivePort('ARP1_a'),
                          AnalogReceivePort('ARP2_a'),
                          AnalogSendPort('A1_a'), AnalogSendPort('A2_a')],
            parameters=['P1_a', 'P2_a']
        )

        b = Dynamics(
            name='A',
            aliases=['A1_b:=P1_b', 'A2_b := ARP1_b + SV2_b', 'A3_b := SV1_b'],
            regimes=[
                Regime(
                    'dSV1_b/dt = -SV1_b / (P2_b*t)',
                    'dSV2_b/dt = SV1_b / (ARP1_b*t) + SV2_b / (P1_b*t)',
                    transitions=[On('SV1_b > P1_b', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1_b',
                ),
                Regime(name='R2_b', transitions=On('SV1_b > 1', to='R1_b'))
            ],
            analog_ports=[AnalogReceivePort('ARP1_b'),
                          AnalogReceivePort('ARP2_b'),
                          AnalogSendPort('A1_b'), AnalogSendPort('A2_b')],
            parameters=['P1_b', 'P2_b']
        )

        for symbol in ('A1', 'A2', 'A3', 'SV1', 'SV2', 'ARP1', 'ARP2', 'P1',
                       'P2', 'R1', 'R2'):
            a.rename_symbol(symbol + '_a', symbol + '_b')
        a == b
        self.assertEqual(a, b,
                         "Symbols were not renamed properly between classes:\n"
                         "{}".format(a.find_mismatch(b)))
