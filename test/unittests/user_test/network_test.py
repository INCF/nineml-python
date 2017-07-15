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
from nineml import Document
from nineml.units import ms, mV, nA, Hz, Mohm
from os import path
from nineml.serialization.xml import XMLUnserializer

src_dir = os.path.dirname(__file__)


class TestNetwork(unittest.TestCase):
    """
    Loads Brunel 2000 network and reads and writes it from XML
    """

    order = 1000
    delay = 1.5 * ms     # (ms) global delay for all neurons in the group
    J = 0.1              # (mV) EPSP size
    Jeff = 24.0 * J      # (nA) synaptic weight
    g = 5.0              # relative strength of inhibitory synapses
    Je = Jeff            # excitatory weights
    Ji = -g * Je         # inhibitory weights
    theta = 20.0 * mV         # firing thresholds
    tau = 20.0 * ms           # membrane time constant
    tau_syn = 0.5 * ms        # synapse time constant
    input_rate = 50.0 * Hz    # mean input spiking rate

    xml_dir = path.normpath(path.join(src_dir, '..', '..', 'xml', 'networks',
                                      'Brunel2000'))

    def setUp(self):
        all_to_all = ConnectionRuleProperties(
            "AllToAll", path.join(self.xml_dir, "AllToAll.xml"), {})

        celltype = DynamicsProperties(
            name="nrn",
            definition=path.join(self.xml_dir, 'BrunelIaF.xml'),
            properties={'tau': self.tau, 'theta': self.theta,
                        'tau_rp': 2.0 * ms, 'Vreset': 10.0 * mV,
                        'R': 1.5 * Mohm},
            initial_values={"V": 0.0 * mV,
                            "t_rpend": 0.0 * ms})
        ext_stim = DynamicsProperties(
            name="stim",
            definition=path.join(self.xml_dir, "Poisson.xml"),
            properties={'rate': self.input_rate},
            initial_values={"t_next": 0.5 * ms})
        psr = DynamicsProperties(
            name="syn",
            definition=path.join(self.xml_dir, "AlphaPSR.xml"),
            properties={'tau_syn': self.tau_syn},
            initial_values={"A": 0.0 * nA, "B": 0.0 * nA})

        p1 = Population("Exc", self.order * 4, celltype)
        p2 = Population("Inh", self.order, celltype)
        inpt = Population("Ext", self.order * 5, ext_stim)

        static_exc = DynamicsProperties(
            "ExcitatoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"), {},
            initial_values={"weight": self.Je * nA})
        static_inh = DynamicsProperties(
            "InhibitoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"),
            initial_values={"weight": self.Ji * nA})

        exc_prj = Projection(
            "Excitation", pre=inpt, post=p1, response=psr,
            plasticity=static_exc, connectivity=all_to_all, delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        inh_prj = Projection(
            "Inhibition", pre=inpt, post=p2, response=psr,
            plasticity=static_inh, connectivity=all_to_all, delay=self.delay,
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        self.model = Network("brunel_network")
        self.model.add(inpt)
        self.model.add(p1)
        self.model.add(p2)
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
