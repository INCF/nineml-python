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
    PropertySet, Projection, Network, DynamicsProperties,
    ConnectionRuleProperties, Population)
from nineml import Document, load
from nineml.units import ms, mV, nA, Hz, Mohm
from os import path

src_dir = os.path.dirname(__file__)


class TestNetwork(unittest.TestCase):
    """
    Loads Brunel 2000 network and reads and writes it from XML
    """

    xml_dir = path.normpath(path.join(src_dir, '..', '..', '..', '..',
                                      'examples', '_old', 'Brunel2000'))

    def test_xml_roundtrip(self):

        delay = 1.5          # (ms) global delay for all neurons in the group
        J = 0.1              # (mV) EPSP size
        Jeff = 24.0 * J      # (nA) synaptic weight
        g = 5.0              # relative strength of inhibitory synapses
#         eta = 2.0            # nu_ext / nu_thresh
        Je = Jeff            # excitatory weights
        Ji = -g * Je         # inhibitory weights
        theta = 20.0         # firing thresholds
        tau = 20.0           # membrane time constant
        tau_syn = 0.5        # synapse time constant
        input_rate = 50.0    # mean input spiking rate

        neuron_parameters = PropertySet(tau=(tau, ms),
                                                theta=(theta, mV),
                                                tau_rp=(2.0, ms),
                                                Vreset=(10.0, mV),
                                                R=(1.5, Mohm))
        psr_parameters = PropertySet(tau_syn=(tau_syn, ms))
        neuron_initial_values = {"V": (0.0, mV),  # todo: use random distr.
                                 "t_rpend": (0.0, ms)}
        synapse_initial_values = {"A": (0.0, nA), "B": (0.0, nA)}
        celltype = DynamicsProperties("nrn",
                                      path.join(self.xml_dir, 'BrunelIaF.xml'),
                                      properties=neuron_parameters,
                                      initial_values=neuron_initial_values)
        ext_stim = DynamicsProperties("stim",
                                      path.join(self.xml_dir, "Poisson.xml"),
                                      PropertySet(rate=(input_rate, Hz)),
                                      initial_values={"t_next": (0.5, ms)})
        psr = DynamicsProperties("syn",
                                 path.join(self.xml_dir, "AlphaPSR.xml"),
                                 properties=psr_parameters,
                                 initial_values=synapse_initial_values)

        p1 = Population("Exc", 1, celltype, positions=None)
        p2 = Population("Inh", 1, celltype, positions=None)
        inpt = Population("Ext", 1, ext_stim, positions=None)

        all_to_all = ConnectionRuleProperties(
            "AllToAll", path.join(self.xml_dir, "AllToAll.xml"), {})
        static_exc = DynamicsProperties(
            "ExcitatoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"), {},
            initial_values={"weight": (Je, nA)})
        static_inh = DynamicsProperties(
            "InhibitoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"),
            initial_values={"weight": (Ji, nA)})

        exc_prj = Projection(
            "Excitation", pre=inpt, post=p1, response=psr,
            plasticity=static_exc, connectivity=all_to_all, delay=(delay, ms),
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        inh_prj = Projection(
            "Inhibition", pre=inpt, post=p2, response=psr,
            plasticity=static_inh, connectivity=all_to_all, delay=(delay, ms),
            port_connections=[('response', 'Isyn', 'post', 'Isyn'),
                              ('plasticity', 'weight', 'response', 'weight')])
        model = Network("brunel_network")
        model.add(inpt, p1, p2)
        model.add(exc_prj, inh_prj)
        doc = Document(model, static_exc, static_inh, exc_prj,
                       inh_prj, ext_stim, psr, p1, p2, inpt, celltype)
        xml = doc.to_xml()
        loaded_doc = load(xml)
        if loaded_doc != doc:
            mismatch = loaded_doc.find_mismatch(doc)
        else:
            mismatch = ''
        self.assertEqual(loaded_doc, doc,
                         "Brunel network model failed xml roundtrip:\n\n{}"
                         .format(mismatch))
