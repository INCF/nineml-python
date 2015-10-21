from nineml import units as un
from nineml import abstraction as al  # @Reimport
from lxml import etree


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
        name="aeIF",
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


if __name__ == '__main__':
    print etree.tostring(
        create_adaptive_exponential().to_xml(),
        encoding="UTF-8", pretty_print=True, xml_declaration=True)
