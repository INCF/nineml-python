# encoding: utf-8
"""
Test of the 9ML components for the Brunel (2000) network model
by simulating a network of three neurons.

This script imports a Python lib9ml network description from
"brunel_network_components_test.py", exports it as XML, and then
runs a simulation using the pyNN.nineml module with the NEURON
backend.

"""
from __future__ import division
import os.path
import unittest
from nineml.abstraction import ConnectionRule
from nineml import Document
from nineml.serialization.xml import XMLUnserializer
from nineml.abstraction import (
    Dynamics, Parameter, AnalogSendPort, AnalogReducePort, StateVariable,
    EventSendPort, OnCondition, Regime, TimeDerivative, StateAssignment,
    OutputEvent, Constant, OnEvent, AnalogReceivePort, EventReceivePort)
from nineml.user import (
    DynamicsProperties, Population,
    Projection, ConnectionRuleProperties,
    Network, Selection, Concatenate)
import nineml.units as un


src_dir = os.path.dirname(__file__)


class TestNetwork(unittest.TestCase):
    """
    Loads Brunel 2000 network and reads and writes it from XML
    """

    order = 1000
    delay = 1.5 * un.ms     # (ms) global delay for all neurons in the group
    J = 0.1              # (mV) EPSP size
    Jeff = 24.0 * J      # (nA) synaptic weight
    g = 5.0              # relative strength of inhibitory synapses
    Je = Jeff            # excitatory weights
    Ji = -g * Je         # inhibitory weights
    theta = 20.0 * un.mV         # firing thresholds
    tau = 20.0 * un.ms           # membrane time constant
    tau_syn = 0.5 * un.ms        # synapse time constant
    input_rate = 50.0 * un.Hz    # mean input spiking rate

    def setUp(self):
        liaf = Dynamics(
            name='liaf',
            parameters=[
                Parameter(name='R', dimension=un.resistance),
                Parameter(name='Vreset', dimension=un.voltage),
                Parameter(name='tau', dimension=un.time),
                Parameter(name='tau_rp', dimension=un.time),
                Parameter(name='theta', dimension=un.voltage)],
            analog_ports=[
                AnalogReducePort(name='Isyn', dimension=un.current,
                                 operator='+'),
                AnalogSendPort(name='V', dimension=un.voltage),
                AnalogSendPort(name='t_rpend', dimension=un.time)],
            event_ports=[
                EventSendPort(name='spikeOutput')],
            state_variables=[
                StateVariable(name='V', dimension=un.voltage),
                StateVariable(name='t_rpend', dimension=un.time)],
            regimes=[
                Regime(
                    name='refractoryRegime',
                    transitions=[
                        OnCondition(
                            't > t_rpend',
                            target_regime='subthresholdRegime')]),
                Regime(
                    name='subthresholdRegime',
                    time_derivatives=[
                        TimeDerivative('V', '(Isyn*R - V)/tau')],
                    transitions=[
                        OnCondition(
                            'V > theta',
                            target_regime='refractoryRegime',
                            state_assignments=[
                                StateAssignment('V', 'Vreset'),
                                StateAssignment('t_rpend', 't + tau_rp')],
                            output_events=[
                                OutputEvent('spikeOutput')])])])

        poisson = Dynamics(
            name='Poisson',
            parameters=[Parameter(name='rate', dimension=un.per_time)],
            event_ports=[EventSendPort(name='spikeOutput')],
            state_variables=[StateVariable(name='t_next', dimension=un.time)],
            regimes=[
                Regime(
                    name='default',
                    transitions=[
                        OnCondition(
                            't > t_next',
                            target_regime='default',
                            state_assignments=[
                                StateAssignment(
                                    't_next',
                                    'one_ms*random.exponential('
                                    'rate*thousand_milliseconds) + t')],
                            output_events=[
                                OutputEvent('spikeOutput')])])],
                 constants=[
                     Constant(name='one_ms', units=un.ms, value=1.0),
                     Constant(name='thousand_milliseconds', units=un.ms,
                              value=1000.0)])

        static = Dynamics(
            name='StaticConnection',
            analog_ports=[
                AnalogSendPort(name='weight', dimension=un.current)],
            state_variables=[
                StateVariable(name='weight', dimension=un.current)],
            regimes=[
                Regime(name='default',
                       time_derivatives=[
                           TimeDerivative('weight', 'zero')])],
            constants=[Constant(name='zero', units=un.A / un.s, value=0.0)])

        psr = Dynamics(
            name='AlphaPSR',
            parameters=[
                Parameter(name='tau_syn', dimension=un.time)],
            event_ports=[EventReceivePort(name='spike')],
            analog_ports=[
                AnalogReceivePort(name='weight', dimension=un.current),
                AnalogSendPort(name='A', dimension=un.current),
                AnalogSendPort(name='B', dimension=un.current),
                AnalogSendPort(name='Isyn', dimension=un.current)],
            state_variables=[
                StateVariable(name='A', dimension=un.current),
                StateVariable(name='B', dimension=un.current)],
            regimes=[
                Regime(
                    name='default',
                    time_derivatives=[
                        TimeDerivative('A', '(-A + B)/tau_syn'),
                        TimeDerivative('B', '-B/tau_syn')],
                    transitions=[
                        OnEvent(
                            'spike',
                            target_regime='default',
                            state_assignments=[
                                StateAssignment('B', 'B + weight')])])],
            aliases=['Isyn:=A'])

        all_to_all_class = ConnectionRule(
            'AllToAllClass', standard_library=(
                "http://nineml.net/9ML/1.0/connectionrules/AllToAll"))

        all_to_all = ConnectionRuleProperties(
            "AllToAll", all_to_all_class, {})

        celltype = DynamicsProperties(
            name="liaf_props",
            definition=liaf,
            properties={'tau': self.tau, 'theta': self.theta,
                        'tau_rp': 2.0 * un.ms, 'Vreset': 10.0 * un.mV,
                        'R': 1.5 * un.Mohm},
            initial_values={"V": 0.0 * un.mV,
                            "t_rpend": 0.0 * un.ms})
        ext_stim = DynamicsProperties(
            name="stim",
            definition=poisson,
            properties={'rate': self.input_rate},
            initial_values={"t_next": 0.5 * un.ms})

        psr = DynamicsProperties(
            name="syn",
            definition=psr,
            properties={'tau_syn': self.tau_syn},
            initial_values={"A": 0.0 * un.nA, "B": 0.0 * un.nA})

        exc = Population("Exc", self.order * 4, celltype)
        inh = Population("Inh", self.order, celltype)
        ext = Population("Ext", self.order * 5, ext_stim)
        exc_and_inh = Selection("All", Concatenate(exc, inh))

        static_ext = DynamicsProperties(
            "ExternalPlasticity",
            static, {}, initial_values={"weight": self.Je * un.nA})

        static_exc = DynamicsProperties(
            "ExcitatoryPlasticity",
            static, {}, initial_values={"weight": self.Je * un.nA})

        static_inh = DynamicsProperties(
            "InhibitoryPlasticity",
            static, initial_values={"weight": self.Ji * un.nA})

        ext_prj = Projection(
            "External", pre=ext, post=exc_and_inh, response=psr,
            plasticity=static_ext, connectivity=all_to_all, delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])

        exc_prj = Projection(
            "Excitation", pre=ext, post=exc, response=psr,
            plasticity=static_exc, connectivity=all_to_all, delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        inh_prj = Projection(
            "Inhibition", pre=ext, post=inh, response=psr,
            plasticity=static_inh, connectivity=all_to_all, delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        self.model = Network("brunel_network")
        self.model.add(ext)
        self.model.add(exc)
        self.model.add(inh)
        self.model.add(ext_prj)
        self.model.add(exc_prj)
        self.model.add(inh_prj)

    def test_scale(self):
        pass

    def test_delay_limits(self):
        pass

    def test_components(self):
        pass

    def test_resample_connectivity(self):
        pass

    def test_connectivity_has_been_sampled(self):
        pass

#     def get_components(self):
#         components = []
#         for p in chain(self.populations.values(), self.projections.values()):
#             components.extend(p.get_components())
#         return components
# 
#     def resample_connectivity(self, *args, **kwargs):
#         for projection in self.projections:
#             projection.resample_connectivity(*args, **kwargs)
# 
#     def connectivity_has_been_sampled(self):    
#         return any(p.connectivity.has_been_sampled() for p in self.projections)

    def test_xml_roundtrip(self):

        doc = Document(self.model)  # , static_exc, static_inh, exc_prj, inh_prj, ext_stim, psr, p1, p2, inpt, celltype) @IgnorePep8
        xml = doc.serialize()
        loaded_doc = XMLUnserializer(root=xml).unserialize()
        if loaded_doc != doc:
            mismatch = loaded_doc.find_mismatch(doc)
        else:
            mismatch = ''
        self.assertEqual(loaded_doc, doc,
                         "Brunel network model failed xml roundtrip:\n\n{}"
                         .format(mismatch))
