# encoding: utf-8
"""
Simulation script for the Brunel (2000) network model as described in NineML.

This script imports a Python lib9ml network description from
"brunel_network_alpha.py", exports it as XML, and then
runs a simulation using the pyNN.nineml module with the NEURON
backend.

"""

from __future__ import division
import sys
import numpy as np
from neo import AnalogSignal
from quantities import ms, dimensionless
import pyNN.neuron as sim
from pyNN.nineml.read import Network
# from pyNN.utility import SimulationProgressBar
from pyNN.utility.plotting import Figure, Panel
from brunel_network_alpha import build_model

case = sys.argv[1] if len(sys.argv) >= 2 else 'SR'
plot_figure = False

parameters = {
    "SR": {"g": 3, "eta": 2},
    "SR2": {"g": 2, "eta": 2},
    "SR3": {"g": 0, "eta": 2},
    "SIfast": {"g": 6, "eta": 4},
    "AI": {"g": 5, "eta": 2},
    "SIslow": {"g": 4.5, "eta": 0.9},
    "SIslow": {"g": 4.5, "eta": 0.95}
}

plot_limits = (900, 1200)


model = build_model(**parameters[case])

xml_file = "brunel_network_alpha_%s.xml" % case
model.write(xml_file)

sim.setup()

print("Building network")
net = Network(sim, xml_file)

if plot_figure:
    stim = net.populations["Ext"]
    stim[:100].record('spikes')
    exc = net.populations["Exc"]
    exc.sample(50).record("spikes")
    exc.sample(3).record(["nrn_V", "syn_A"])
    inh = net.populations["Inh"]
    inh.sample(50).record("spikes")
    inh.sample(3).record(["nrn_V", "syn_A"])
else:
    all = net.assemblies["All neurons"]
    #all.sample(50).record("spikes")
    all.record("spikes")

print("Running simulation")
t_stop = plot_limits[1]
# pb = SimulationProgressBar(t_stop/80, t_stop)

sim.run(t_stop)#, callbacks=[pb])

print("Handling data")
if plot_figure:
    stim_data = stim.get_data().segments[0]
    exc_data = exc.get_data().segments[0]
    inh_data = inh.get_data().segments[0]
else:
    all.write_data("brunel_network_alpha_%s.h5" % case)

sim.end()


def instantaneous_firing_rate(segment, begin, end):
    """Computed in bins of 0.1 ms """
    bins = np.arange(begin, end, 0.1)
    hist, _ = np.histogram(segment.spiketrains[0].time_slice(begin, end), bins)
    for st in segment.spiketrains[1:]:
        h, _ = np.histogram(st.time_slice(begin, end), bins)
        hist += h
    return AnalogSignal(hist, sampling_period=0.1*ms, units=dimensionless,
                        channel_index=0, name="Spike count")

if plot_figure:
    Figure(
        Panel(stim_data.spiketrains, markersize=0.2, xlim=plot_limits),
        Panel(exc_data.analogsignalarrays[0], yticks=True, xlim=plot_limits),
        Panel(exc_data.analogsignalarrays[1], yticks=True, xlim=plot_limits),
        Panel(exc_data.spiketrains[:100], markersize=0.5, xlim=plot_limits),
        Panel(instantaneous_firing_rate(exc_data, *plot_limits), yticks=True),
        Panel(inh_data.analogsignalarrays[0], yticks=True, xlim=plot_limits),
        Panel(inh_data.analogsignalarrays[1], yticks=True, xlim=plot_limits),
        Panel(inh_data.spiketrains[:100], markersize=0.5, xlim=plot_limits),
        Panel(instantaneous_firing_rate(inh_data, *plot_limits), xticks=True, xlabel="Time (ms)", yticks=True),
    ).save("brunel_network_alpha.png")
