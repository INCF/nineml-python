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
import unittest
import nineml.user_layer as nineml
from nineml.abstraction_layer.units import ms, mV, nA, Hz, Mohm


class TestNetwork(unittest.TestCase):
    """
    Loads Brunel 2000 network and reads and writes it from XML
    """

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

        celltype = nineml.SpikingNodeType("nrn", "BrunelIaF.xml",
                                          neuron_parameters,
                                          initial_values=neuron_initial_values)
        ext_stim = nineml.SpikingNodeType("stim", "Poisson.xml",
                                          nineml.PropertySet(rate=(input_rate,
                                                                   Hz)),
                                          initial_values={"t_next": (0.5, ms)})
        psr = nineml.SynapseType("syn", "AlphaPSR.xml", psr_parameters,
                                 initial_values=synapse_initial_values)

        p1 = nineml.Population("Exc", 1, celltype, positions=None)
        p2 = nineml.Population("Inh", 1, celltype, positions=None)
        inpt = nineml.Population("Ext", 1, ext_stim, positions=None)

        all_to_all = nineml.ConnectionRule("AllToAll", "AllToAll.xml")

        static_exc = nineml.ConnectionType("ExcitatoryPlasticity",
                                           "StaticConnection.xml",
                                           initial_values={"weight": (Je, nA)})
        static_inh = nineml.ConnectionType("InhibitoryPlasticity",
                                           "StaticConnection.xml",
                                           initial_values={"weight": (Ji, nA)})

        exc_prj = nineml.Projection("Excitation", inpt, p1,
                                    connectivity=all_to_all,
                                    response=psr,
                                    plasticity=static_exc,
                                    port_connections=[
                                        nineml.PortConnection("plasticity",
                                                              "response",
                                                              "weight", "q"),
                                        nineml.PortConnection("response",
                                                              "destination",
                                                              "Isyn",
                                                              "Isyn")],
                                    delay=(delay, ms))

        inh_prj = nineml.Projection("Inhibition", inpt, p2,
                                    connectivity=all_to_all,
                                    response=psr,
                                    plasticity=static_inh,
                                    port_connections=[
                                        nineml.PortConnection("plasticity",
                                                              "response",
                                                              "weight", "q"),
                                        nineml.PortConnection("response",
                                                              "destination",
                                                              "Isyn",
                                                              "Isyn")],
                                    delay=(delay, ms))

        model = nineml.Network("Three-neuron network with alpha synapses")
        model.add(input, p1, p2)
        model.add(exc_prj, inh_prj)

        with open() as f:
            self.model.write(f)
        loaded_model = nineml.Network.load(f)
        self.assertEqual(loaded_model, self.model)
