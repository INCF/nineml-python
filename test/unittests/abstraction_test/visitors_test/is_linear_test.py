import unittest
from nineml.abstraction import (
    Dynamics, Regime, Parameter, AnalogReceivePort, Constant,
    OnCondition, AnalogReducePort, EventReceivePort, OnEvent, StateAssignment,
    AnalogSendPort)
from nineml import units as un


class DynamicsIsLinearTest(unittest.TestCase):

    def test_basic_linear(self):
        """A basic linear dynamics example"""
        a = Dynamics(
            name='A',
            regimes=[
                Regime('dSV1/dt = -SV1 / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless)])
        self.assertTrue(a.is_linear())

    def test_multi_regime_nonlinear(self):
        """Nonlinear due to multiple regimes"""
        b = Dynamics(
            name='B',
            regimes=[
                Regime('dSV1/dt = -SV1 / P1',
                       transitions=[OnEvent('ERP1', target_regime_name='R2')],
                       name='R1'),
                Regime('dSV1/dt = -SV1 / P1',
                       transitions=[OnEvent('ERP1', target_regime_name='R1')],
                       name='R2')],
            event_ports=[EventReceivePort('ERP1')],
            parameters=[Parameter('P1', dimension=un.time)])
        self.assertFalse(b.is_linear())

    def test_on_condition_state_assignment_nonlinear(self):
        """
        Nonlinear due to a state assignment in on-condition (i.e. piece-wise
        dynamics
        """
        c = Dynamics(
            name='C',
            regimes=[
                Regime('dSV1/dt = -P1 * SV1',
                       transitions=[OnCondition(
                           'SV1 > 10',
                           state_assignments=[StateAssignment('SV1', 20)])],
                       name='R1')],
            parameters=[Parameter('P1', dimension=un.per_time)])
        self.assertFalse(c.is_linear())

    def test_input_multiplication_nonlinear(self):
        """Nonlinear due to multiplication of SV1 and SV2 in SV1 T.D."""
        d = Dynamics(
            name='D',
            regimes=[
                Regime('dSV1/dt = -SV1 * SV2 / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless)])
        self.assertFalse(d.is_linear())

    def test_output_filtering(self):
        """
        Tests whether the 'outputs' argument is able to filter (presumably)
        unconnected nonlinear mappings from inputs and states to analog send
        ports
        """
        e = Dynamics(
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
        self.assertFalse(e.is_linear())
        self.assertTrue(e.is_linear(outputs=['A1']))

    def test_linear_state_assignment_in_onevent(self):
        """Test linear state assignments in on events"""
        f = Dynamics(
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
        self.assertTrue(f.is_linear())

    def test_nonlinear_state_assignment_in_onevent(self):
        """Test that nonlinear state assignements in on events"""
        g = Dynamics(
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
        self.assertFalse(g.is_linear())

    def test_nonlinear_function(self):
        """Nonlinear due function in SV1 T.D."""
        h = Dynamics(
            name='H',
            regimes=[
                Regime('dSV1/dt = -sin(SV1) / P1',
                       'dSV2/dt = -SV2 / P1 + ARP1 * P2', name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.per_time)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.dimensionless)])
        self.assertFalse(h.is_linear())
