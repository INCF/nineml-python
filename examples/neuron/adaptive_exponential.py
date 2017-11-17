from __future__ import division
from nineml import units as un
from nineml import abstraction as al, user as ul


def create_adaptive_exponential():
    """
    Adaptive exponential integrate-and-fire neuron as described in
    A. Destexhe, J COmput Neurosci 27: 493--506 (2009)

    Author B. Kriener (Jan 2011)

    ## neuron model: aeIF

    ## variables:
    ## V: membrane potential
    ## w: adaptation variable

    ## parameters:
    ## C_m     # specific membrane capacitance [muF/cm**2]
    ## g_L     # leak conductance [mS/cm**2]
    ## E_L     # resting potential [mV]
    ## Delta   # steepness of exponential approach to threshold [mV]
    ## V_T     # spike threshold [mV]
    ## S       # membrane area [mum**2]
    ## trefractory # refractory time [ms]
    ## tspike  # spike time [ms]
    ## tau_w   # adaptation time constant
    ## a, b    # adaptation parameters [muS, nA]
    """
    aeIF = al.Dynamics(
        name="AdaptiveExpIntegrateAndFire",
        parameters=[
            al.Parameter('C_m', un.capacitance),
            al.Parameter('g_L', un.conductance),
            al.Parameter('E_L', un.voltage),
            al.Parameter('Delta', un.voltage),
            al.Parameter('V_T', un.voltage),
            al.Parameter('S'),
            al.Parameter('trefractory', un.time),
            al.Parameter('tspike', un.time),
            al.Parameter('tau_w', un.time),
            al.Parameter('a', un.dimensionless / un.voltage),
            al.Parameter('b')],
        state_variables=[
            al.StateVariable('V', un.voltage),
            al.StateVariable('w')],
        regimes=[
            al.Regime(
                name="subthresholdregime",
                time_derivatives=[
                    "dV/dt = -g_L*(V-E_L)/C_m + Isyn/C_m + g_L*Delta*exp((V-V_T)/Delta-w/S)/C_m",  # @IgnorePep8
                    "dw/dt = (a*(V-E_L)-w)/tau_w", ],
                transitions=al.On("V > V_T",
                                  do=["V = E_L", "w = w + b",
                                      al.OutputEvent('spikeoutput')],
                                  to="refractoryregime")),
            al.Regime(
                name="refractoryregime",
                transitions=al.On("t>=tspike+trefractory",
                                  to="subthresholdregime"))],
        analog_ports=[al.AnalogReducePort("Isyn", un.current, operator="+")])
    return aeIF


def parameterise_adaptive_exponential(definition=None):
    if definition is None:
        definition = create_adaptive_exponential()
    comp = ul.DynamicsProperties(
        name='SampleAdaptiveExpIntegrateAndFire',
        definition=definition,
        properties=[ul.Property('C_m', 1 * un.pF),
                    ul.Property('g_L', 0.1 * un.nS),
                    ul.Property('E_L', -65 * un.mV),
                    ul.Property('Delta', 1 * un.mV),
                    ul.Property('V_T', -58 * un.mV),
                    ul.Property('S', 0.1),
                    ul.Property('tspike', 0.5 * un.ms),
                    ul.Property('trefractory', 0.25 * un.ms),
                    ul.Property('tau_w', 4 * un.ms),
                    ul.Property('a', 1 * un.per_mV),
                    ul.Property('b', 2)],
        initial_values=[ul.Initial('V', -70 * un.mV),
                        ul.Initial('w', 0.1 * un.mV)])
    return comp
