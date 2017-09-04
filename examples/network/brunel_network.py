# encoding: utf-8
"""
Network model from

    Brunel, N. (2000) J. Comput. Neurosci. 8: 183-208

expressed in NineML using the Python API

Author: Andrew P. Davison, UNIC, CNRS
June 2014
    Edited by Thomas G. Close, October 2015
"""

from __future__ import division
from nineml.user import (
    DynamicsProperties, Population, RandomDistributionProperties,
    Projection, ConnectionRuleProperties, AnalogPortConnection,
    EventPortConnection, Network, Selection, Concatenate)
from nineml.units import ms, mV, nA, unitless, Hz, Mohm
import ninemlcatalog


def create_brunel(g, eta, name=None):
    """
    Build a NineML representation of the Brunel (2000) network model.

    Arguments:
        g: relative strength of inhibitory synapses
        eta: nu_ext / nu_thresh

    Returns:
        a nineml user layer Model object
    """
    # Meta-parameters
    order = 1000       # scales the size of the network
    Ne = 4 * order     # number of excitatory neurons
    Ni = 1 * order     # number of inhibitory neurons
    epsilon = 0.1      # connection probability
    Ce = int(epsilon * Ne)  # number of excitatory synapses per neuron
    Ci = int(epsilon * Ni)  # number of inhibitory synapses per neuron
    Cext = Ce          # effective number of external synapses per neuron
    delay = 1.5        # (ms) global delay for all neurons in the group
    J = 0.1            # (mV) EPSP size
    Jeff = 24.0 * J      # (nA) synaptic weight
    Je = Jeff          # excitatory weights
    Ji = -g * Je       # inhibitory weights
    Jext = Je          # external weights
    theta = 20.0       # firing thresholds
    tau = 20.0         # membrane time constant
    tau_syn = 0.1      # synapse time constant
    # nu_thresh = theta / (Je * Ce * tau * exp(1.0) * tau_syn) # threshold rate
    nu_thresh = theta / (J * Ce * tau)
    nu_ext = eta * nu_thresh      # external rate per synapse
    input_rate = 1000.0 * nu_ext * Cext   # mean input spiking rate

    # Parameters
    neuron_parameters = dict(tau=tau * ms,
                             v_threshold=theta * mV,
                             refractory_period=2.0 * ms,
                             v_reset=10.0 * mV,
                             R=1.5 * Mohm)  # units??
    psr_parameters = dict(tau=tau_syn * ms)

    # Initial Values
    v_init = RandomDistributionProperties(
        "uniform_rest_to_threshold",
        ninemlcatalog.load("randomdistribution/Uniform",
                           'UniformDistribution'),
        {'minimum': (0.0, unitless),
         'maximum': (theta, unitless)})
#     v_init = 0.0
    neuron_initial_values = {"v": (v_init * mV),
                             "refractory_end": (0.0 * ms)}
    synapse_initial_values = {"a": (0.0 * nA), "b": (0.0 * nA)}
    tpoisson_init = RandomDistributionProperties(
        "exponential_beta",
        ninemlcatalog.load('randomdistribution/Exponential',
                           'ExponentialDistribution'),
        {"rate": (1000.0 / input_rate * unitless)})
#     tpoisson_init = 5.0

    # Dynamics components
    celltype = DynamicsProperties(
        "nrn",
        ninemlcatalog.load('neuron/LeakyIntegrateAndFire',
                           'LeakyIntegrateAndFire'),
        neuron_parameters, initial_values=neuron_initial_values)
    ext_stim = DynamicsProperties(
        "stim",
        ninemlcatalog.load('input/Poisson', 'Poisson'),
        dict(rate=(input_rate, Hz)),
        initial_values={"t_next": (tpoisson_init, ms)})
    psr = DynamicsProperties(
        "syn",
        ninemlcatalog.load('postsynapticresponse/Alpha', 'Alpha'),
        psr_parameters,
        initial_values=synapse_initial_values)

    # Connecion rules
    one_to_one_class = ninemlcatalog.load(
        '/connectionrule/OneToOne', 'OneToOne')
    random_fan_in_class = ninemlcatalog.load(
        '/connectionrule/RandomFanIn', 'RandomFanIn')

    # Populations
    exc_cells = Population("Exc", Ne, celltype, positions=None)
    inh_cells = Population("Inh", Ni, celltype, positions=None)
    external = Population("Ext", Ne + Ni, ext_stim, positions=None)

    # Selections
    all_cells = Selection(
        "All", Concatenate((exc_cells, inh_cells)))

    # Projections
    input_prj = Projection(
        "External", external, all_cells,
        connection_rule_properties=ConnectionRuleProperties(
            "OneToOne", one_to_one_class),
        response=psr,
        plasticity=DynamicsProperties(
            "ExternalPlasticity",
            ninemlcatalog.load("plasticity/Static", 'Static'),
            properties={"weight": (Jext, nA)}),
        port_connections=[
            EventPortConnection(
                'pre', 'response', 'spike_output', 'spike'),
            AnalogPortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            AnalogPortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    exc_prj = Projection(
        "Excitation", exc_cells, all_cells,
        connection_rule_properties=ConnectionRuleProperties(
            "RandomExc", random_fan_in_class, {"number": (Ce * unitless)}),
        response=psr,
        plasticity=DynamicsProperties(
            "ExcitatoryPlasticity",
            ninemlcatalog.load("plasticity/Static", 'Static'),
            properties={"weight": (Je, nA)}),
        port_connections=[
            EventPortConnection(
                'pre', 'response', 'spike_output', 'spike'),
            AnalogPortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            AnalogPortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    inh_prj = Projection(
        "Inhibition", inh_cells, all_cells,
        connection_rule_properties=ConnectionRuleProperties(
            "RandomInh", random_fan_in_class, {"number": (Ci * unitless)}),
        response=psr,
        plasticity=DynamicsProperties(
            "InhibitoryPlasticity",
            ninemlcatalog.load("plasticity/Static", 'Static'),
            properties={"weight": (Ji, nA)}),
        port_connections=[
            EventPortConnection(
                'pre', 'response', 'spike_output', 'spike'),
            AnalogPortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            AnalogPortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    # Save to document in NineML Catalog
    network = Network(name if name else "BrunelNetwork")
    network.add(exc_cells, inh_cells, external, all_cells, input_prj, exc_prj,
                inh_prj)
    return network
