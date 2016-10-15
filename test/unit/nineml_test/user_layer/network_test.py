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
import nineml.user as nineml
from nineml.units import ms, mV, nA, Hz, Mohm
from os import path

src_dir = os.path.dirname(__file__)


class TestNetwork(unittest.TestCase):
    """
    Loads Brunel 2000 network and reads and writes it from XML
    """

    tmp_xml_file = path.join(src_dir, 'network_tmp.xml')
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

        neuron_parameters = nineml.PropertySet(tau=(tau, ms),
                                                theta=(theta, mV),
                                                tau_rp=(2.0, ms),
                                                Vreset=(10.0, mV),
                                                R=(1.5, Mohm))
        psr_parameters = nineml.PropertySet(tau_syn=(tau_syn, ms))
        neuron_initial_values = {"V": (0.0, mV),  # todo: use random distr.
                                 "t_rpend": (0.0, ms)}
        synapse_initial_values = {"A": (0.0, nA), "B": (0.0, nA)}

        celltype = nineml.SpikingNodeType("nrn",
                                          path.join(self.xml_dir,
                                                    'BrunelIaF.xml'),
                                          properties=neuron_parameters,
                                          initial_values=neuron_initial_values)
        ext_stim = nineml.SpikingNodeType("stim",
                                          path.join(self.xml_dir,
                                                    "Poisson.xml"),
                                          nineml.PropertySet(rate=(input_rate,
                                                                   Hz)),
                                          initial_values={"t_next": (0.5, ms)})
        psr = nineml.SynapseType("syn",
                                 path.join(self.xml_dir, "AlphaPSR.xml"),
                                 properties=psr_parameters,
                                 initial_values=synapse_initial_values)

        p1 = nineml.Population("Exc", 1, celltype, positions=None)
        p2 = nineml.Population("Inh", 1, celltype, positions=None)
        inpt = nineml.Population("Ext", 1, ext_stim, positions=None)

        all_to_all = nineml.Connectivity(
            "AllToAll", path.join(self.xml_dir, "AllToAll.xml"), {})

        static_exc = nineml.DynamicsProperties(
            "ExcitatoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"), {},
            initial_values={"weight": (Je, nA)})
        static_inh = nineml.DynamicsProperties(
            "InhibitoryPlasticity",
            path.join(self.xml_dir, "StaticConnection.xml"),
            initial_values={"weight": (Ji, nA)})

        exc_prj = nineml.Projection(
            "Excitation", inpt,
            (p1, nineml.PortConnection('Isyn', nineml.FromResponse('Isyn'))),
            response=(psr, nineml.PortConnection(
                'weight', nineml.FromPlasticity('weight'))),
            plasticity=static_exc,
            connectivity=all_to_all,
            delay=(delay, ms))

        inh_prj = nineml.Projection(
            "Inhibition", inpt,
            (p2, nineml.PortConnection('Isyn', nineml.FromResponse('Isyn'))),
            response=(psr, nineml.PortConnection(
                'weight', nineml.FromPlasticity('weight'))),
            plasticity=static_inh,
            connectivity=all_to_all,
            delay=(delay, ms))

        model = nineml.Network("Three-neuron network with alpha synapses")
        model.add(inpt, p1, p2)
        model.add(exc_prj, inh_prj)
        model.write(self.tmp_xml_file)
        loaded_model = nineml.Network.read(self.tmp_xml_file)
        self.assertEqual(loaded_model, model)
        os.remove(self.tmp_xml_file)
