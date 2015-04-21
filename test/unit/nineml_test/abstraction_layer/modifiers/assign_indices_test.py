from copy import copy
import unittest
from nineml.abstraction_layer.dynamics import (
    Dynamics, Regime, On, OutputEvent)
from nineml.abstraction_layer.ports import AnalogSendPort, AnalogReceivePort


class DynamicsAssignIndices_test(unittest.TestCase):

    def test_after_cloning(self):

        a = Dynamics(
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

        b = copy(a)
        for symbol in ('A1', 'A2', 'A3', 'SV1', 'SV2', 'ARP1', 'ARP2', 'P1',
                       'P2', 'R1', 'R2'):
            if symbol.startswith('ARP'):
                dname = 'analog_receive_port'
            elif symbol.startswith('A'):
                dname = 'alias'
            elif symbol.startswith('P'):
                dname = 'parameter'
            elif symbol.startswith('R'):
                dname = 'regime'
            elif symbol.startswith('SV1'):
                dname = 'state_variable'
            a_elem = getattr(a, dname)(symbol)
            b_elem = getattr(b, dname)(symbol)
            self.assertEqual(a.index_of(a_elem), b.index_of(b_elem),
                             "Index of '{}' {} was not preserved after cloning"
                             "({} before, {} after)"
                             .format(symbol, a_elem.__class__.__name__,
                                     a.index_of(a_elem), b.index_of(b_elem)))
        self.assertEqual(a, b,
                         "Symbols were not renamed properly between classes")
