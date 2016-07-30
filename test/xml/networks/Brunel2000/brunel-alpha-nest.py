# -*- coding: utf-8 -*-
#
# brunel-alpha-nest.py
#
# This file is part of NEST.
#
# Copyright (C) 2004 The NEST Initiative
#
# NEST is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NEST is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NEST.  If not, see <http://www.gnu.org/licenses/>.

# This version uses NEST's Connect functions.

import sys
from scipy.optimize import fsolve
import nest
import nest.raster_plot

import neo
import numpy as np
import time
from numpy import exp


case = sys.argv[1]

parameters = {
    "SR": {"g": 3.0, "eta": 2.0},
    "SR2": {"g": 2.0, "eta": 2.0},
    "SR3": {"g": 0.0, "eta": 2.0},
    "SIfast": {"g": 6.0, "eta": 4.0},
    "AI": {"g": 5.0, "eta": 2.0},
    "SIslow": {"g": 4.5, "eta": 0.9},
    "SIslow": {"g": 4.5, "eta": 0.95}
}


def ComputePSPnorm(tauMem, CMem, tauSyn):
  """Compute the maximum of postsynaptic potential
     for a synaptic input current of unit amplitude
     (1 pA)"""

  a = (tauMem / tauSyn)
  b = (1.0 / tauSyn - 1.0 / tauMem)

  # time of maximum
  t_max = 1.0/b * ( -nest.sli_func('LambertWm1',-exp(-1.0/a)/a) - 1.0/a )

  # maximum of PSP for current of unit amplitude
  return exp(1.0)/(tauSyn*CMem*b) * ((exp(-t_max/tauMem) - exp(-t_max/tauSyn)) / b - t_max*exp(-t_max/tauSyn))


nest.ResetKernel()

startbuild = time.time()

dt      = 0.1    # the resolution in ms
simtime = 1200.0 # Simulation time in ms
delay   = 1.5    # synaptic delay in ms

# Parameters for asynchronous irregular firing
g       = parameters[case]["g"]
eta     = parameters[case]["eta"]
epsilon = 0.1  # connection probability

order     = 2500
NE        = 4*order
NI        = 1*order
N_neurons = NE+NI
N_rec     = order//2

CE    = int(epsilon*NE) # number of excitatory synapses per neuron
CI    = int(epsilon*NI) # number of inhibitory synapses per neuron  
C_tot = int(CI+CE)      # total number of synapses per neuron

# Initialize the parameters of the integrate and fire neuron
tauSyn = 0.5
tauMem = 20.0
CMem = 250.0
theta  = 20.0
J      = 0.1 # postsynaptic amplitude in mV

# normalize synaptic current so that amplitude of a PSP is J
J_unit = ComputePSPnorm(tauMem, CMem, tauSyn)
J_ex  = J / J_unit
J_in  = -g*J_ex

# threshold rate, equivalent rate of events needed to
# have mean input current equal to threshold
nu_th  = (theta * CMem) / (J_ex*CE*exp(1)*tauMem*tauSyn)
nu_ex  = eta*nu_th
p_rate = 1000.0*nu_ex*CE

nest.SetKernelStatus({"resolution": dt, "print_time": True, 'local_num_threads': 1})

print("Building network")

neuron_params= {"C_m":        CMem,
                "tau_m":      tauMem,
                "tau_syn_ex": tauSyn,
                "tau_syn_in": tauSyn,
                "t_ref":      2.0,
                "E_L":        0.0,
                "V_reset":    0.0,
                "V_m":        0.0,
                "V_th":       theta}

nest.SetDefaults("iaf_psc_alpha", neuron_params)

nodes_ex=nest.Create("iaf_psc_alpha",NE)
nodes_in=nest.Create("iaf_psc_alpha",NI)

nest.SetDefaults("poisson_generator",{"rate": p_rate})
noise=nest.Create("poisson_generator")

espikes=nest.Create("spike_detector")
ispikes=nest.Create("spike_detector")

nest.SetStatus(espikes,[{"label": "brunel-py-ex",
                   "withtime": True,
                   "withgid": True}])

nest.SetStatus(ispikes,[{"label": "brunel-py-in",
                   "withtime": True,
                   "withgid": True}])

print("Connecting devices")

nest.CopyModel("static_synapse","excitatory",{"weight":J_ex, "delay":delay})
nest.CopyModel("static_synapse","inhibitory",{"weight":J_in, "delay":delay})

nest.Connect(noise,nodes_ex, 'all_to_all', "excitatory")
nest.Connect(noise,nodes_in,'all_to_all', "excitatory")

nest.Connect(range(1,N_rec+1),espikes, 'all_to_all', "excitatory")
nest.Connect(range(NE+1,NE+1+N_rec),ispikes, 'all_to_all', "excitatory")

print("Connecting network")

# We now iterate over all neuron IDs, and connect the neuron to
# the sources from our array. The first loop connects the excitatory neurons
# and the second loop the inhibitory neurons.

print("Excitatory connections")

conn_params_ex = {'rule': 'fixed_indegree', 'indegree': CE}
nest.Connect(nodes_ex, nodes_ex+nodes_in, conn_params_ex, "excitatory")

print("Inhibitory connections")

conn_params_in = {'rule': 'fixed_indegree', 'indegree': CI}
nest.Connect(nodes_in, nodes_ex+nodes_in, conn_params_in, "inhibitory")

endbuild=time.time()

print("Simulating")

nest.Simulate(simtime)

endsimulate= time.time()

events_ex = nest.GetStatus(espikes,"n_events")[0]
rate_ex   = events_ex/simtime*1000.0/N_rec
events_in = nest.GetStatus(ispikes,"n_events")[0]
rate_in   = events_in/simtime*1000.0/N_rec

num_synapses = nest.GetDefaults("excitatory")["num_connections"]+\
nest.GetDefaults("inhibitory")["num_connections"]

build_time = endbuild-startbuild
sim_time   = endsimulate-endbuild

print("Brunel network simulation (Python)")
print("Parameter set     : {}".format(case))
print("Number of neurons : {0}".format(N_neurons))
print("Number of synapses: {0}".format(num_synapses))
print("       Exitatory  : {0}".format(int(CE * N_neurons) + N_neurons))
print("       Inhibitory : {0}".format(int(CI * N_neurons)))
print("Excitatory rate   : %.2f Hz" % rate_ex)
print("Inhibitory rate   : %.2f Hz" % rate_in)
print("Building time     : %.2f s" % build_time)
print("Simulation time   : %.2f s" % sim_time)


def spike_detector_to_neo(spike_detector, t_stop, label=""):
    """
    Convert the spikes recorded by NEST to a Neo Block
    """
    from datetime import datetime

    segment = neo.Segment(name=label, rec_datetime=datetime.now())
    segment.spiketrains = []
    events = nest.GetStatus(spike_detector, 'events')[0]
    ids = events['senders']
    values = events['times']
    for id in np.unique(ids):
        spike_times = values[ids==id]
        segment.spiketrains.append(
            neo.SpikeTrain(spike_times,
                           t_start=0.0,
                           t_stop=t_stop,
                           units='ms',
                           source_id=int(id)))
    data = neo.Block(name=label)
    data.segments.append(segment)
    return data

data = spike_detector_to_neo(espikes, simtime)
neo.get_io("brunel-alpha-nest-%s.h5" % case).write(data)
