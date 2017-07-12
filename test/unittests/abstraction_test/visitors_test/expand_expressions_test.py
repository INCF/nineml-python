import unittest
from nineml.abstraction import (
    Dynamics, Regime, Alias, Parameter, AnalogReceivePort, AnalogReducePort,
    OnCondition)
from nineml.abstraction.dynamics.visitors.queriers import (
    DynamicsSubstituteAliasQuerier)
from nineml import units as un


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsRequiredDefinitions_test(unittest.TestCase):

    def setUp(self):

        self.a = Dynamics(
            name='A',
            aliases=['A1:=P1 / P2', 'A2 := ARP2 + P3', 'A3 := A4 * P4 * P5',
                     'A4:=P6 ** 2 + ADP1'],
            regimes=[
                Regime('dSV1/dt = -A1 / A2',
                       'dSV2/dt = -ADP1 / P7',
                       'dSV3/dt = -A1 / A2',
                       transitions=[OnCondition('SV1 > 10',
                                                target_regime='R2')],
                       aliases=[Alias('A1', 'P1 / P2 * 2')],
                       name='R1'),
                Regime('dSV1/dt = -A1 / A2',
                       'dSV3/dt = -A1 / A2 * A4',
                       transitions=[OnCondition('SV1 < 10',
                                                target_regime='R1')],
                       name='R2')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.resistance),
                          AnalogReceivePort('ARP2', dimension=un.charge),
                          AnalogReducePort('ADP1',
                                           dimension=un.dimensionless)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.resistance),
                        Parameter('P3', dimension=un.charge),
                        Parameter('P4', dimension=un.length / un.current ** 2),
                        Parameter('P5', dimension=un.current ** 2 / un.length),
                        Parameter('P6', dimension=un.dimensionless),
                        Parameter('P7', dimension=un.time)]
        )

        self.ref_expanded_a = None

    def test_expand_expressions(self):
        expanded_a = DynamicsSubstituteAliasQuerier(self.a, 'new_a').expanded
        self.assertEqual(expanded_a, self.ref_expanded_a,
                         expanded_a.find_mismatch(self.ref_expanded_a))
