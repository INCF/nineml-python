import unittest
from nineml.abstraction import (
    Parameter, Dynamics, Alias, EventSendPort, AnalogSendPort, StateVariable,
    Regime, TimeDerivative, OnCondition, OutputEvent)
from nineml import Document
import nineml.units as un


class TestAnnotations(unittest.TestCase):

    def test_indices_annotations(self):
        a = Dynamics(
            name='a',
            parameters=[Parameter('P1'), Parameter('P2'), Parameter('P3')],
            ports=[AnalogSendPort('ASP1'), AnalogSendPort('ASP2'),
                   EventSendPort('ESP1'), EventSendPort('ESP2'),
                   EventSendPort('ESP3')],
            state_variables=[StateVariable('SV3'),
                             StateVariable('SV1'),
                             StateVariable('SV2')],
            regimes=[Regime(name='R1',
                            time_derivatives=[
                                TimeDerivative('SV2', 'SV2/t'),
                                TimeDerivative('SV1', 'SV2/t')],
                            transitions=[
                                OnCondition('SV1 > P1',
                                            output_events=[
                                                OutputEvent('ESP2'),
                                                OutputEvent('ESP1')]),
                                OnCondition('SV2 < P2 + P3',
                                            output_events=[
                                                OutputEvent('ESP3')],
                                            target_regime_name='R2')]),
                     Regime(name='R2',
                            time_derivatives=[
                                TimeDerivative('SV3', 'SV3/t')],
                            transitions=[
                                OnCondition('SV3 > 100',
                                            output_events=[
                                                OutputEvent('ESP3'),
                                                OutputEvent('ESP2')],
                                            target_regime_name='R1')])],
            aliases=[Alias('ASP1', 'SV1+SV2'),
                     Alias('ASP2', 'SV2+SV3')])
        # Set indices of parameters in non-ascending order so that they
        # can be differentiated from indices on read.
        a.index_of(a.parameter('P1'))
        a.index_of(a.parameter('P3'))
        a.index_of(a.parameter('P2'))
        a.index_of(a.event_send_port('ESP2'))
        a.index_of(a.event_send_port('ESP1'))
        doc = Document(un.dimensionless)
        serialised = a.serialize(document=doc, save_indices=True,
                                 version=self.version)
        re_a = Dynamics.unserialize(serialised, format='xml',
                                    version=self.version, document=doc)
        self.assertEqual(re_a.index_of(re_a.parameter('P1')),
                         a.index_of(a.parameter('P1')))
        self.assertEqual(re_a.index_of(re_a.parameter('P2')),
                         a.index_of(a.parameter('P2')))
        self.assertEqual(re_a.index_of(re_a.parameter('P3')),
                         a.index_of(a.parameter('P3')))
        self.assertEqual(re_a.index_of(re_a.event_send_port('ESP1')),
                         a.index_of(a.event_send_port('ESP1')))
        self.assertEqual(re_a.index_of(re_a.event_send_port('ESP2')),
                         a.index_of(a.event_send_port('ESP2')))
