import unittest
from nineml.abstraction import (
    Dynamics, Regime, Alias, Parameter, AnalogReceivePort)
from nineml import units as un


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsRequiredDefinitions_test(unittest.TestCase):

    def setUp(self):

        self.a = Dynamics(
            name='A',
            aliases=['A1:=P1 / P2', 'A2 := ARP2 + P3', 'A3 := P4 * P5'],
            regimes=[
                Regime('dSV1/dt = -A1 / A2',
                       aliases=[Alias('A1', 'P1 / P2 * 2')],
                       name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.resistance),
                          AnalogReceivePort('ARP2', dimension=un.charge)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.resistance),
                        Parameter('P3', dimension=un.charge),
                        Parameter('P4', dimension=un.length / un.current ** 2),
                        Parameter('P5', dimension=un.current ** 2 / un.length)]
        )

    def test_dimension_resolutions(self):
        self.assertEquals(self.a.dimension_of('P1'), un.voltage)
        self.assertEquals(self.a.dimension_of(self.a.element('P1')), un.voltage)
        self.assertEquals(self.a.dimension_of('SV1'), un.dimensionless)
        self.assertEquals(self.a.dimension_of('A1'), un.current)
        self.assertEquals(self.a.dimension_of('A2'), un.charge)
        self.assertEquals(self.a.dimension_of('A3'), un.dimensionless)
