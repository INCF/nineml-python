from __future__ import division
import unittest
from nineml.abstraction import (
    Parameter, Dynamics, Regime, On, OutputEvent, StateVariable,
    StateAssignment, AnalogSendPort, AnalogReceivePort,
    ConnectionRule)
from nineml.user import (
    Population, DynamicsProperties, Projection, ConnectionRuleProperties)
from nineml.xmlns import NINEML
from nineml import units as un, Document


class TestProjection(unittest.TestCase):

    def setUp(self):
        self.pre_dynamics = Dynamics(
            name='PreDynamics',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P1',
                    transitions=[On('SV1 > P2', do=[OutputEvent('emit')])],
                    name='R1'
                ),
            ],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.voltage)]
        )

        self.post_dynamics = Dynamics(
            name='PostDynamics',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P1 + ARP1 / P2',
                    name='R1'
                ),
            ],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.capacitance)]
        )

        self.response_dynamics = Dynamics(
            name='ResponseDynamics',
            state_variables=[
                StateVariable('SV1', dimension=un.current)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P1',
                    transitions=[On('receive',
                                    do=[StateAssignment('SV1', 'SV1 + P2')])],
                    name='R1'
                ),
            ],
            analog_ports=[AnalogSendPort('SV1', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.current)]
        )

        self.pre = Population(
            name="Population1",
            size=1,
            cell=DynamicsProperties(
                name="PreDynamicsProps", definition=self.pre_dynamics,
                properties={'P1': (1, un.ms), 'P2': (-65, un.mV)}))

        self.post = Population(
            name="Population1",
            size=1,
            cell=DynamicsProperties(
                name="PostDynamicsProps", definition=self.post_dynamics,
                properties={'P1': (1, un.ms), 'P2': (1, un.uF)}))

        self.one_to_one = ConnectionRule(
            name="OneToOne",
            standard_library=(NINEML + 'connectionrules/OneToOne'))

        self.projection = Projection(
            name="Projection",
            pre=self.pre, post=self.post,
            response=DynamicsProperties(
                name="ResponseProps",
                definition=self.response_dynamics,
                properties={'P1': (10, un.ms), 'P2': (1, un.nA)}),
            connectivity=ConnectionRuleProperties(
                name="ConnectionRuleProps",
                definition=self.one_to_one),
            delay=(1, un.ms))

    def test_xml_roundtrip(self):
        document = Document()
        xml = self.projection.to_xml()
        projection2 = Projection.from_xml(xml, document)
        self.assertEquals(self.projection, projection2,
                          "Projection failed XML roundtrip")

if __name__ == '__main__':
    tester = TestProjection()
    tester.test_xml_roundtrip()
