import unittest
from nineml.abstraction import (
    Dynamics, Regime, Alias, Parameter, AnalogReceivePort, AnalogReducePort,
    OnCondition, AnalogSendPort, Constant, StateAssignment)
from nineml.abstraction.dynamics.visitors.modifiers import (
    DynamicsSubstituteAliases)
from nineml import units as un


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsSubstituteAliasesTest(unittest.TestCase):

    def setUp(self):

        self.a = Dynamics(
            name='A',
            aliases=['A1:=P1 / P2', 'A2 := ARP2 + P3', 'A3 := A4 * P4 * P5',
                     'A4:=P6 ** 2 + ADP1', 'A5:=SV1 * SV2 * P8',
                     'A6:=SV1 * P1 / P8', 'A7:=A1 / P8'],
            regimes=[
                Regime('dSV1/dt = -A1 / A2',
                       'dSV2/dt = -ADP1 / P7',
                       'dSV3/dt = -A1 * A3 / (A2 * C1)',
                       transitions=[OnCondition('SV1 > 10',
                                                target_regime='R2')],
                       aliases=[Alias('A1', 'P1 / P2 * 2'),
                                Alias('A5', 'SV1 * SV2 * P8 * 2')],
                       name='R1'),
                Regime('dSV1/dt = -A1 / A2',
                       'dSV3/dt = -A1 / A2 * A4',
                       transitions=[OnCondition(
                           'C2 > A6',
                           state_assignments=[
                               StateAssignment('SV1', 'SV1 - A7')],
                           target_regime='R1')],
                       name='R2')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.resistance),
                          AnalogReceivePort('ARP2', dimension=un.charge),
                          AnalogReducePort('ADP1',
                                           dimension=un.dimensionless),
                          AnalogSendPort('A5', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.resistance),
                        Parameter('P3', dimension=un.charge),
                        Parameter('P4', dimension=un.length / un.current ** 2),
                        Parameter('P5', dimension=un.current ** 2 / un.length),
                        Parameter('P6', dimension=un.dimensionless),
                        Parameter('P7', dimension=un.time),
                        Parameter('P8', dimension=un.current)],
            constants=[Constant('C1', value=10.0, units=un.unitless),
                       Constant('C2', value=1.0, units=un.ohm)])

        self.ref_substituted_a = Dynamics(
            name='substituted_A',
            aliases=['A5:=SV1 * SV2 * P8'],
            regimes=[
                Regime('dSV1/dt = -2 * (P1 / P2) / (ARP2 + P3)',
                       'dSV2/dt = -ADP1 / P7',
                       ('dSV3/dt = -2 * (P1 / P2) * ((P6 ** 2 + ADP1) * P4 * '
                        'P5) / ((ARP2 + P3) * C1)'),
                       transitions=[OnCondition('SV1 > 10',
                                                target_regime='R2')],
                       aliases=[Alias('A5', 'SV1 * SV2 * P8 * 2')],
                       name='R1'),
                Regime('dSV1/dt = -(P1 / P2) / (ARP2 + P3)',
                       'dSV3/dt = -(P1 / P2) / (ARP2 + P3) * (P6 ** 2 + ADP1)',
                       transitions=[OnCondition(
                           'C2 > (SV1 * P1 / P8)',
                           state_assignments=[
                               StateAssignment('SV1', 'SV1 - (P1 / P2) / P8')],
                           target_regime='R1')],
                       name='R2')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.resistance),
                          AnalogReceivePort('ARP2', dimension=un.charge),
                          AnalogReducePort('ADP1',
                                           dimension=un.dimensionless),
                          AnalogSendPort('A5', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.resistance),
                        Parameter('P3', dimension=un.charge),
                        Parameter('P4', dimension=un.length / un.current ** 2),
                        Parameter('P5', dimension=un.current ** 2 / un.length),
                        Parameter('P6', dimension=un.dimensionless),
                        Parameter('P7', dimension=un.time),
                        Parameter('P8', dimension=un.current)],
            constants=[Constant('C1', value=10.0, units=un.unitless),
                       Constant('C2', value=1.0, units=un.ohm)]
        )

    def test_substitute_aliases(self):
        substituted_a = self.a.clone()
        substituted_a.name = 'substituted_A'
        DynamicsSubstituteAliases(substituted_a)
        self.assertEqual(substituted_a, self.ref_substituted_a,
                         substituted_a.find_mismatch(self.ref_substituted_a))
