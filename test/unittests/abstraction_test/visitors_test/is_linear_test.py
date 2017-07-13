import unittest
from nineml.abstraction import (
    Dynamics, Regime, Parameter, AnalogReceivePort,
    OnCondition, EventReceivePort, OnEvent, StateAssignment)
from nineml import units as un


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsSubstituteAliasesTest(unittest.TestCase):

    def setUp(self):

        self.a = Dynamics(
            name='A',
            regimes=[
                Regime('dSV1/dt = -SV1 / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless)])

        self.b = Dynamics(
            name='B',
            regimes=[
                Regime('dSV1/dt = -SV1 / P1',
                       transitions=[OnEvent('ERP1', target_regime='R2')],
                       name='R1'),
                Regime('dSV1/dt = -SV1 / P1',
                       transitions=[OnEvent('ERP1', target_regime='R1')],
                       name='R2')],
            event_ports=[EventReceivePort('ERP1')],
            parameters=[Parameter('P1', dimension=un.time)])

        self.c = Dynamics(
            name='C',
            regimes=[
                Regime('dSV1/dt = -P1 * SV1',
                       transitions=[OnCondition(
                           'SV1 > 10',
                           state_assignments=[StateAssignment('SV1', 20)])],
                       name='R1')],
            parameters=[Parameter('P1', dimension=un.per_time)])

        self.d = Dynamics(
            name='D',
            regimes=[
                Regime('dSV1/dt = -SV1 * SV2 / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless)])

    def test_is_linear(self):
        self.assertTrue(self.a.is_linear())
        self.assertFalse(self.b.is_linear())
        self.assertFalse(self.c.is_linear())
        self.assertFalse(self.d.is_linear())
