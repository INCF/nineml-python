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
from nineml.abstraction import (
    Dynamics, Parameter, AnalogSendPort, AnalogReducePort, StateVariable,
    EventSendPort, OnCondition, Regime, TimeDerivative, StateAssignment,
    OutputEvent, Constant, OnEvent, AnalogReceivePort, EventReceivePort,
    RandomDistribution)
from nineml.user import (
    DynamicsProperties, Population,
    Projection, ConnectionRuleProperties, RandomDistributionProperties,
    Network, Selection, Concatenate)
from nineml.values import RandomDistributionValue
import nineml.units as un
from nineml.exceptions import NineMLRandomDistributionDelayException


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

        one_to_one_class = ConnectionRule(
            'OneToOneClass', standard_library=(
                "http://nineml.net/9ML/1.0/connectionrules/OneToOne"))

        self.one_to_one = ConnectionRuleProperties(
            "OneToOne", one_to_one_class, {})

        random_fan_in_class = ConnectionRule(
            name="RandomFanIn",
            parameters=[
                Parameter(name="number")],
            standard_library=(
                "http://nineml.net/9ML/1.0/connectionrules/RandomFanIn"))

        exc_random_fan_in = ConnectionRuleProperties(
            name="RandomFanInProps",
            definition=random_fan_in_class,
            properties={'number': 100})

        inh_random_fan_in = ConnectionRuleProperties(
            name="RandomFanInProps",
            definition=random_fan_in_class,
            properties={'number': 200})

        self.celltype = DynamicsProperties(
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

        self.psr = DynamicsProperties(
            name="syn",
            definition=psr,
            properties={'tau_syn': self.tau_syn},
            initial_values={"A": 0.0 * un.nA, "B": 0.0 * un.nA})

        exc = Population("Exc", self.order * 4, self.celltype)
        inh = Population("Inh", self.order, self.celltype)
        ext = Population("Ext", self.order * 5, ext_stim)
        exc_and_inh = Selection("All", Concatenate(exc, inh))

        self.static_ext = DynamicsProperties(
            "ExternalPlasticity",
            static, {}, initial_values={"weight": self.Je * un.nA})

        static_exc = DynamicsProperties(
            "ExcitatoryPlasticity",
            static, {}, initial_values={"weight": self.Je * un.nA})

        static_inh = DynamicsProperties(
            "InhibitoryPlasticity",
            static, initial_values={"weight": self.Ji * un.nA})

        ext_prj = Projection(
            "External", pre=ext, post=exc_and_inh, response=self.psr,
            plasticity=self.static_ext, connectivity=self.one_to_one,
            delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])

        exc_prj = Projection(
            "Excitation", pre=exc, post=exc_and_inh, response=self.psr,
            plasticity=static_exc, connectivity=exc_random_fan_in,
            delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        inh_prj = Projection(
            "Inhibition", pre=inh, post=exc_and_inh, response=self.psr,
            plasticity=static_inh, connectivity=inh_random_fan_in,
            delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        self.model = Network("brunel_network")
        self.model.add(ext)
        self.model.add(exc)
        self.model.add(inh)
        self.model.add(exc_and_inh)
        self.model.add(ext_prj)
        self.model.add(exc_prj)
        self.model.add(inh_prj)

    def test_scale(self):
        new_order = 100
        scale = new_order / self.order
        scaled = self.model.scale(scale)
        self.assertEqual(scaled.population('Ext').size, new_order * 5)
        self.assertEqual(scaled.population('Exc').size, new_order * 4)
        self.assertEqual(scaled.population('Inh').size, new_order)
        self.assertEqual(scaled.selection('All').size, new_order * 5)
        self.assertEqual(
            scaled.projection('External').connectivity.source_size,
            new_order * 5)
        self.assertEqual(
            scaled.projection('Excitation').connectivity.source_size,
            new_order * 4)
        self.assertEqual(
            scaled.projection('Inhibition').connectivity.source_size,
            new_order)
        self.assertEqual(
            scaled.projection('External').connectivity.destination_size,
            new_order * 5)
        self.assertEqual(
            scaled.projection('Excitation').connectivity.destination_size,
            new_order * 5)
        self.assertEqual(
            scaled.projection('Inhibition').connectivity.destination_size,
            new_order * 5)
        self.assertEqual(len(scaled.projection('External')), new_order * 5)
        # NB: The number of connections is scaled on both both by the number
        # of connections made in each "fan" and the number of neurons in
        # populations
        self.assertEqual(len(scaled.projection('Excitation')),
                         int(100 * scale) * new_order * 5)
        self.assertEqual(len(scaled.projection('Inhibition')),
                         int(200 * scale) * new_order * 5)

    def test_delay_limits(self):
        limits = self.model.delay_limits()
        self.assertEqual(limits['min_delay'], 1.5 * un.ms)
        self.assertEqual(limits['max_delay'], 1.5 * un.ms)

    def test_delay_no_projs(self):
        simple_network = Network(
            name='simple',
            populations=[self.model.population('Exc')])
        zero_limits = simple_network.delay_limits()
        self.assertEqual(zero_limits['min_delay'], 0.0 * un.s)
        self.assertEqual(zero_limits['max_delay'], 0.0 * un.s)

    def test_delay_rand_distr(self):

        rand_delay_class = RandomDistribution(
            name="RandomDelay",
            parameters=[
                Parameter('mean', dimension=un.dimensionless),
                Parameter('stddev', dimension=un.dimensionless)],
            standard_library=(
                'http://www.uncertml.org/distributions/normal'))

        pop1 = Population("Pop1", 100, self.celltype)
        pop2 = Population("Pop2", 100, self.celltype)

        rand_delay = RandomDistributionProperties(
            name="RandomDelayProps",
            definition=rand_delay_class,
            properties={'mean': 5.0,
                        'stddev': 1.0})

        rand_delay_prj = Projection(
            "External", pre=pop1, post=pop2, response=self.psr,
            plasticity=self.static_ext, connectivity=self.one_to_one,
            delay=RandomDistributionValue(rand_delay) * un.ms,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        rand_distr_network = Network('rand_distr_net',
                                     populations=[pop1, pop2],
                                     projections=[rand_delay_prj])
        self.assertRaises(
            NineMLRandomDistributionDelayException,
            rand_distr_network.delay_limits)

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
