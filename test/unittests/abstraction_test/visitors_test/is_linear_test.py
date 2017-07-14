import unittest
from nineml.abstraction import (
    Dynamics, Regime, Parameter, AnalogReceivePort, Constant,
    OnCondition, AnalogReducePort, EventReceivePort, OnEvent, StateAssignment,
    AnalogSendPort)
from nineml import units as un


class DynamicsIsLinearTest(unittest.TestCase):

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

        self.e = Dynamics(
            name='E',
            regimes=[
                Regime('dSV1/dt = -SV1 / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1')],
            aliases=['A1:=SV1 * C1', 'A2:=SV1 * SV2'],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time),
                          AnalogSendPort('A1', dimension=un.current),
                          AnalogSendPort('A2', dimension=un.dimensionless)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless)],
            constants=[Constant('C1', 10, units=un.mA)])

        self.f = Dynamics(
            name='F',
            regimes=[
                Regime('dSV1/dt = -SV1 / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1',
                       transitions=[
                           OnEvent('ERP1', state_assignments=[
                               StateAssignment('SV2', 'SV2 + A2')])])],
            aliases=['A1:=SV1 * C1', 'A2:=P3 * P4'],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time),
                          AnalogSendPort('A1', dimension=un.current),
                          AnalogSendPort('A2', dimension=un.dimensionless)],
            event_ports=[EventReceivePort('ERP1')],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless),
                        Parameter('P3', dimension=un.resistance),
                        Parameter('P4', dimension=un.conductance)],
            constants=[Constant('C1', 10, units=un.pA)])

        self.g = Dynamics(
            name='G',
            regimes=[
                Regime('dSV1/dt = -SV1 / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1',
                       transitions=[
                           OnEvent('ERP1', state_assignments=[
                               StateAssignment('SV2', 'SV2 + A2')])])],
            aliases=['A1:=SV1 * C1', 'A2:=P3 * P4 / ADP1'],
            analog_ports=[AnalogReceivePort('ARP1',
                                            dimension=un.per_time),
                          AnalogReducePort('ADP1', operator='+',
                                            dimension=un.dimensionless),
                          AnalogSendPort('A1', dimension=un.current),
                          AnalogSendPort('A2', dimension=un.dimensionless)],
            event_ports=[EventReceivePort('ERP1')],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless),
                        Parameter('P3', dimension=un.resistance),
                        Parameter('P4', dimension=un.conductance)],
            constants=[Constant('C1', 10, units=un.nA)])

        self.h = Dynamics(
            name='H',
            regimes=[
                Regime('dSV1/dt = -sin(SV1) / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless)])

    def test_is_linear(self):
        self.assertTrue(self.a.is_linear())
        self.assertFalse(self.b.is_linear())
        self.assertFalse(self.c.is_linear())
        self.assertFalse(self.d.is_linear())
        self.assertFalse(self.e.is_linear())
        self.assertTrue(self.e.is_linear(outputs=['A1']))
        self.assertTrue(self.f.is_linear())
        self.assertFalse(self.g.is_linear())
        self.assertFalse(self.h.is_linear())
