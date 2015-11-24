# encoding: utf-8
"""
Network model from

    Brunel, N. (2000) J. Comput. Neurosci. 8: 183-208

expressed using PyNN.

Author: Andrew P. Davison, UNIC, CNRS
June 2014
"""

from __future__ import division
from math import exp
from pyNN.random import NumpyRNG, RandomDistribution
from pyNN.utility import ProgressBar
import pyNN.neuron as sim

order = 2500        # scales the size of the network
Ne = 4 * order     # number of excitatory neurons
Ni = 1 * order     # number of inhibitory neurons
epsilon = 0.1      # connectivity probability
Ce = epsilon * Ne  # total number of excitatory synapses
Ci = epsilon * Ni  # total number of inhibitory synapses
Cext = Ce          # total number of external synapses
delay = 1.5        # (ms) global delay for all neurons in the group
v2i = 25.0         # (nA) synaptic weight needed to give a voltage change of approx 1 mV
J = 0.1 * v2i      # (nA) synaptic weight
g = 5.0            # relative strength of inhibitory synapses
eta = 2.0          # nu_ext / nu_thresh
Je = J             # excitatory weights
Ji = -g * Je       # inhibitory weights
Jext = Je          # external weights
theta = 20.0       # firing thresholds
tau = 20.0         # membrane time constant
tau_syn = 0.5      # synapse time constant
nu_thresh = theta * v2i / (Je * Ce * tau * exp(1.0) * tau_syn)  # threshold rate
nu_ext = eta * nu_thresh      # external rate per synapse
input_rate = 1000.0 * nu_ext  # mean input spiking rate
v_init = RandomDistribution("uniform", (theta/2, theta), rng=NumpyRNG(seed=79845634))

sim.setup()

celltype = sim.IF_curr_alpha(tau_m=tau, v_thresh=theta,
                             tau_refrac=2.0, v_reset=10.0,
                             v_rest=0.0, cm=tau/1.5,
                             tau_syn_E=tau_syn, tau_syn_I=tau_syn)

ext_stim = sim.SpikeSourcePoisson(rate=input_rate)

exc_cells = sim.Population(Ne, celltype, initial_values={'v': v_init}, label="Exc")
inh_cells = sim.Population(Ni, celltype, initial_values={'v': v_init}, label="Inh")
external = sim.Population(int(Cext), ext_stim, label="Ext")

all_cells = exc_cells + inh_cells

all_to_all = sim.AllToAllConnector(callback=ProgressBar())
random_uniform = sim.FixedProbabilityConnector(p_connect=epsilon, callback=ProgressBar())

static_ext = sim.StaticSynapse(delay=delay, weight=Jext)
static_exc = sim.StaticSynapse(delay=delay, weight=Je)
static_inh = sim.StaticSynapse(delay=delay, weight=Ji)

input_prj = sim.Projection(external, all_cells, all_to_all,
                           synapse_type=static_ext, receptor_type="excitatory",
                           label="External")
exc_prj = sim.Projection(exc_cells, all_cells, random_uniform,
                         synapse_type=static_exc, receptor_type="excitatory",
                         label="Excitation")
inh_prj = sim.Projection(inh_cells, all_cells, random_uniform,
                         synapse_type=static_inh, receptor_type="inhibitory",
                         label="Inhibition")

external.sample(50).record("spikes")
all_cells.sample(50).record("spikes")
exc_cells[0:1].record("v")

sim.run(200.0)

input_spikes = external.get_data().segments[0].spiketrains
network_spikes = all_cells.get_data().segments[0].spiketrains
vm = exc_cells.get_data().segments[0].analogsignalarrays[0]

sim.end()


from pyNN.utility.plotting import Figure, Panel
Figure(
    Panel(input_spikes, markersize=1.0),
    Panel(vm),
    Panel(network_spikes, markersize=1.0),
).save("brunel_network_alpha_PyNN_neuron.png")
