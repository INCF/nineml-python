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
import nineml.user
from nineml.units import ms, mV, nA, unitless, Hz, Mohm


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
    neuron_parameters = nineml.user.PropertySet(tau=(tau, ms),
                                                v_threshold=(theta, mV),
                                                refractory_period=(2.0, ms),
                                                v_reset=(10.0, mV),
                                                R=(1.5, Mohm))  # units??
    psr_parameters = nineml.user.PropertySet(tau=(tau_syn, ms))

    # Initial Values
    v_init = nineml.user.RandomDistributionComponent(
        "uniform_rest_to_threshold",
        ninemlcatalog.lookup("randomdistribution/Uniform",
                             'UniformDistribution'),
        {'minimum': (0.0, unitless),
         'maximum': (theta, unitless)})
#     v_init = 0.0
    neuron_initial_values = {"v": (v_init, mV),
                             "refractory_end": (0.0, ms)}
    synapse_initial_values = {"a": (0.0, nA), "b": (0.0, nA)}
    tpoisson_init = nineml.user.RandomDistributionComponent(
        "exponential_beta",
        ninemlcatalog.lookup("randomdistribution/Exponential",
                             'ExponentialDistribution'),
        {"rate": (1000.0 / input_rate, unitless)})
#     tpoisson_init = 5.0

    # Dynamics components
    celltype = nineml.user.SpikingNodeType(
        "nrn",
        ninemlcatalog.lookup('neuron/LeakyIntegrateAndFire',
                             'LeakyIntegrateAndFire'),
        neuron_parameters, initial_values=neuron_initial_values)
    ext_stim = nineml.user.SpikingNodeType(
        "stim",
        ninemlcatalog.lookup('input/Poisson', 'Poisson'),
        nineml.user.PropertySet(rate=(input_rate, Hz)),
        initial_values={"t_next": (tpoisson_init, ms)})
    psr = nineml.user.SynapseType(
        "syn",
        ninemlcatalog.lookup('postsynapticresponse/Alpha', 'Alpha'),
        psr_parameters,
        initial_values=synapse_initial_values)

    # Connecion rules
    one_to_one_class = ninemlcatalog.lookup(
        '/connectionrule/OneToOne', 'OneToOne')
    random_fan_in_class = ninemlcatalog.lookup(
        '/connectionrule/RandomFanIn', 'RandomFanIn')

    # Populations
    exc_cells = nineml.user.Population("Exc", Ne, celltype, positions=None)
    inh_cells = nineml.user.Population("Inh", Ni, celltype, positions=None)
    external = nineml.user.Population("Ext", Ne + Ni, ext_stim, positions=None)

    # Selections
    all_cells = nineml.user.Selection(
        "All", nineml.user.Concatenate(exc_cells, inh_cells))

    # Projections
    input_prj = nineml.user.Projection(
        "External", external, all_cells,
        connectivity=nineml.user.ConnectionRuleComponent(
            "OneToOne", one_to_one_class),
        response=psr,
        plasticity=nineml.user.ConnectionType(
            "ExternalPlasticity",
            ninemlcatalog.lookup("plasticity/Static", 'Static'),
            properties={"weight": (Jext, nA)}),
        port_connections=[
            nineml.user.PortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            nineml.user.PortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    exc_prj = nineml.user.Projection(
        "Excitation", exc_cells, all_cells,
        connectivity=nineml.user.ConnectionRuleComponent(
            "RandomExc", random_fan_in_class, {"number": (Ce, unitless)}),
        response=psr,
        plasticity=nineml.user.ConnectionType(
            "ExcitatoryPlasticity",
            ninemlcatalog.lookup("plasticity/Static", 'Static'),
            properties={"weight": (Je, nA)}),
        port_connections=[
            nineml.user.PortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            nineml.user.PortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    inh_prj = nineml.user.Projection(
        "Inhibition", inh_cells, all_cells,
        connectivity=nineml.user.ConnectionRuleComponent(
            "RandomInh", random_fan_in_class, {"number": (Ci, unitless)}),
        response=psr,
        plasticity=nineml.user.ConnectionType(
            "InhibitoryPlasticity",
            ninemlcatalog.lookup("plasticity/Static", 'Static'),
            properties={"weight": (Ji, nA)}),
        port_connections=[
            nineml.user.PortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            nineml.user.PortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    # Save to document in NineML Catalog
    network = nineml.user.Network(name if name else "BrunelNetwork")
    network.add(exc_cells, inh_cells, external, all_cells, input_prj, exc_prj,
                inh_prj)
    return network


if __name__ == "__main__":
    import ninemlcatalog

    cases = {
        "SR": {"g": 3, "eta": 2},
        "SR2": {"g": 2, "eta": 2},
        "SR3": {"g": 0, "eta": 2},
        "SIfast": {"g": 6, "eta": 4},
        "AI": {"g": 5, "eta": 2},
        "SIslow1": {"g": 4.5, "eta": 0.9},
        "SIslow2": {"g": 4.5, "eta": 0.95}
    }
    for name, params in cases.iteritems():
        network = create_brunel(**params)
        ninemlcatalog.save(nineml.Document(*network.elements),
                           'network/Brunel2000/' + name)
