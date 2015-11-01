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
from nineml.user import (
    Projection, Network, DynamicsProperties, ConnectionRuleProperties,
    Population)
from nineml.abstraction import (
    Parameter, Dynamics, Regime, On, OutputEvent, StateVariable,
    StateAssignment)
from nineml.abstraction.ports import (
    AnalogSendPort, AnalogReceivePort, EventSendPort, EventReceivePort)
from nineml import units as un
from nineml import Document
from nineml.units import ms, mV, nA, Hz, Mohm
from os import path

src_dir = os.path.dirname(__file__)


class TestNetwork(unittest.TestCase):
    """
    Loads Brunel 2000 network and reads and writes it from XML
    """

    xml_dir = path.normpath(path.join(src_dir, '..', '..', '..',
                                      'examples', '_old', 'Brunel2000'))

    def setUp(self):
        self.all_to_all = ConnectionRuleProperties(
            "AllToAll", path.join(self.xml_dir, "AllToAll.xml"), {})

    def test_xml_roundtrip(self):

        delay = 1.5 * ms     # (ms) global delay for all neurons in the group
        J = 0.1              # (mV) EPSP size
        Jeff = 24.0 * J      # (nA) synaptic weight
        g = 5.0              # relative strength of inhibitory synapses
#         eta = 2.0            # nu_ext / nu_thresh
        Je = Jeff            # excitatory weights
        Ji = -g * Je         # inhibitory weights
        theta = 20.0 * mV         # firing thresholds
        tau = 20.0 * ms           # membrane time constant
        tau_syn = 0.5 * ms        # synapse time constant
        input_rate = 50.0 * Hz    # mean input spiking rate

        celltype = DynamicsProperties(
            name="nrn",
            definition=path.join(self.xml_dir, 'BrunelIaF.xml'),
            properties={'tau': tau, 'theta': theta,
                        'tau_rp': 2.0 * ms, 'Vreset': 10.0 * mV,
                        'R': 1.5 * Mohm},
            initial_values={"V": 0.0 * mV,
                            "t_rpend": 0.0 * ms})
        ext_stim = DynamicsProperties(
            name="stim",
            definition=path.join(self.xml_dir, "Poisson.xml"),
            properties={'rate': input_rate},
            initial_values={"t_next": 0.5 * ms})
        psr = DynamicsProperties(
            name="syn",
            definition=path.join(self.xml_dir, "AlphaPSR.xml"),
            properties={'tau_syn': tau_syn},
            initial_values={"A": 0.0 * nA, "B": 0.0 * nA})

        p1 = Population("Exc", 1, celltype)
        p2 = Population("Inh", 1, celltype)
        inpt = Population("Ext", 1, ext_stim)

        static_exc = DynamicsProperties(
            "ExcitatoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"), {},
            initial_values={"weight": Je * nA})
        static_inh = DynamicsProperties(
            "InhibitoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"),
            initial_values={"weight": Ji * nA})

        exc_prj = Projection(
            "Excitation", pre=inpt, post=p1, response=psr,
            plasticity=static_exc, connectivity=self.all_to_all, delay=delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        inh_prj = Projection(
            "Inhibition", pre=inpt, post=p2, response=psr,
            plasticity=static_inh, connectivity=self.all_to_all, delay=delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        model = Network("brunel_network")
        model.add(inpt)
        model.add(p1)
        model.add(p2)
        model.add(exc_prj)
        model.add(inh_prj)
        doc = Document(model, static_exc, static_inh, exc_prj,
                       inh_prj, ext_stim, psr, p1, p2, inpt, celltype)
        xml = doc.to_xml()
        loaded_doc = Document.load(xml)
        if loaded_doc != doc:
            mismatch = loaded_doc.find_mismatch(doc)
        else:
            mismatch = ''
        self.assertEqual(loaded_doc, doc,
                         "Brunel network model failed xml roundtrip:\n\n{}"
                         .format(mismatch))

    def test_dynamics_compilations(self):

        cell1_cls = Dynamics(
            name='Cell',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P1 + ARP1 / P2',
                    transitions=[On('SV1 > P3', do=[OutputEvent('spike')])],
                    name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                          EventSendPort('spike')],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.capacitance),
                        Parameter('P3', dimension=un.voltage)])

        cell2_cls = Dynamics(
            name='Cell',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 ^ 2 / P1 + ARP1 / P2',
                    transitions=[On('SV1 > P3', do=[OutputEvent('spike')])],
                    name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                          EventSendPort('spike')],
            parameters=[Parameter('P1', dimension=un.time * un.voltage),
                        Parameter('P2', dimension=un.capacitance),
                        Parameter('P3', dimension=un.voltage)])

        exc_cls = Dynamics(
            name="Exc",
            aliases=["I_ext := SV1"],
            regimes=[
                Regime(
                    name="default",
                    time_derivatives=[
                        "dSV1/dt = SV1/tau"],
                    transitions=On('spike', do=["SV1 = SV1 + weight"]))],
            state_variables=[
                StateVariable('SV1', dimension=un.current),
            ],
            analog_ports=[AnalogSendPort("I_ext", dimension=un.current),
                          AnalogReceivePort("weight", dimension=un.current)],
            parameters=[Parameter('tau', dimension=un.time)])

        inh_cls = Dynamics(
            name="Inh",
            aliases=["I_ext := SV1"],
            regimes=[
                Regime(
                    name="default",
                    time_derivatives=[
                        "dSV1/dt = SV1/tau"],
                    transitions=On('spike', do=["SV1 = SV1 - weight"]))],
            state_variables=[
                StateVariable('SV1', dimension=un.current),
            ],
            analog_ports=[AnalogSendPort("I_ext", dimension=un.current),
                          AnalogReceivePort("weight", dimension=un.current)],
            parameters=[Parameter('tau', dimension=un.time)])

        static_cls = Dynamics(
            name="Static",
            aliases=["fixed_weight := weight"],
            regimes=[
                Regime(name="default")],
            analog_ports=[AnalogSendPort("fixed_weight",
                                         dimension=un.current)],
            parameters=[Parameter('weight', dimension=un.current)])

        stdp_cls = Dynamics(
            name="PartialStdpGuetig",
            parameters=[
                Parameter(name='tauLTP', dimension=un.time),
                Parameter(name='aLTD', dimension=un.dimensionless),
                Parameter(name='wmax', dimension=un.dimensionless),
                Parameter(name='muLTP', dimension=un.dimensionless),
                Parameter(name='tauLTD', dimension=un.time),
                Parameter(name='aLTP', dimension=un.dimensionless)],
            analog_ports=[
                AnalogReceivePort(dimension=un.dimensionless, name="w"),
                AnalogSendPort(dimension=un.dimensionless, name="wsyn")],
            event_ports=[
                EventReceivePort(name="incoming_spike")],
            state_variables=[
                StateVariable(name='tlast_post', dimension=un.time),
                StateVariable(name='tlast_pre', dimension=un.time),
                StateVariable(name='deltaw', dimension=un.dimensionless),
                StateVariable(name='interval', dimension=un.time),
                StateVariable(name='M', dimension=un.dimensionless),
                StateVariable(name='P', dimension=un.dimensionless),
                StateVariable(name='wsyn', dimension=un.dimensionless)],
            regimes=[
                Regime(
                    name="sole",
                    transitions=On(
                        'incoming_spike',
                        to='sole',
                        do=[
                            StateAssignment('tlast_post', 't'),
                            StateAssignment('tlast_pre', 'tlast_pre'),
                            StateAssignment(
                                'deltaw',
                                'P*pow(wmax - wsyn, muLTP) * '
                                'exp(-interval/tauLTP) + deltaw'),
                            StateAssignment('interval', 't - tlast_pre'),
                            StateAssignment(
                                'M', 'M*exp((-t + tlast_post)/tauLTD) - aLTD'),
                            StateAssignment(
                                'P', 'P*exp((-t + tlast_pre)/tauLTP) + aLTP'),
                            StateAssignment('wsyn', 'deltaw + wsyn')]))])

        exc = DynamicsProperties(
            name="ExcProps",
            definition=exc_cls, properties={'tau': 1 * ms})

        inh = DynamicsProperties(
            name="ExcProps",
            definition=inh_cls, properties={'tau': 1 * ms})

        static = DynamicsProperties(name="StaticProps",
                                    definition=static_cls,
                                    properties={'weight': 1 * un.nA})

        stdp = DynamicsProperties(name="StdpProps", definition=stdp_cls,
                                  properties={'tauLTP': 10 * un.ms,
                                              'aLTD': 1,
                                              'wmax': 2,
                                              'muLTP': 3,
                                              'tauLTD': 20 * un.ms,
                                              'aLTP': 4})

        pop1 = Population(
            name="Pop1",
            size=10,
            cell=DynamicsProperties(
                name="Pop1Props",
                definition=cell1_cls,
                properties={'P1': 10 * un.ms,
                            'P2': 100 * un.uF,
                            'P3': -50 * un.mV}))

        pop2 = Population(
            name="Pop2",
            size=15,
            cell=DynamicsProperties(
                name="Pop2Props",
                definition=cell2_cls,
                properties={'P1': 20 * un.ms * un.mV,
                            'P2': 50 * un.uF,
                            'P3': -40 * un.mV}))

        pop3 = Population(
            name="Pop3",
            size=20,
            cell=DynamicsProperties(
                name="Pop3Props",
                definition=cell1_cls,
                properties={'P1': 30 * un.ms,
                            'P2': 50 * un.pF,
                            'P3': -20 * un.mV}))

        proj1 = Projection(
            name="Proj1", pre=pop1, post=pop2, response=exc, plasticity=static,
            connectivity=self.all_to_all,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('response', 'i_syn', 'post', 'i_ext'),
                ('plasticity', 'fixed_weight', 'response', 'weight')],
            delay=1 * un.ms)

        proj2 = Projection(
            name="Proj2", pre=pop2, post=pop1, response=inh, plasticity=static,
            connectivity=self.all_to_all,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('response', 'i_syn', 'post', 'i_ext'),
                ('plasticity', 'fixed_weight', 'response', 'weight')],
            delay=1 * un.ms)

        proj3 = Projection(
            name="Proj3",
            pre=pop3, post=pop2, response=exc, plasticity=stdp,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('response', 'i_syn', 'post', 'i_ext'),
                ('plasticity', 'fixed_weight', 'response', 'weight')],
            delay=1 * un.ms)

        proj4 = Projection(
            name="Proj4",
            pre=pop3, post=pop1, response=exc, plasticity=static,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('response', 'i_syn', 'post', 'i_ext'),
                ('plasticity', 'fixed_weight', 'response', 'weight')],
            delay=1 * un.ms)

        network = Network(
            name="Net",
            populations=(pop1, pop2, pop3),
            projections=(proj1, proj2, proj3, proj4))

        print network
