from nineml import abstraction as al  # @Reimport
from nineml import units as un
from lxml import etree


def create_hodgkin_huxley():
    """A Hodgkin-Huxley single neuron model.
    Written by Andrew Davison.
    See http://phobos.incf.ki.se/src_rst/
              examples/examples_al_python.html#example-hh
    """
    aliases = [
        "q10 := 3.0**((celsius - qfactor)/tendegrees)",  # temperature correction factor @IgnorePep8
        "alpha_m := alpha_m_A*(V-alpha_m_V0)/(exp(-(V-alpha_m_V0)/alpha_m_K) - 1.0)",  # @IgnorePep8
        "beta_m := beta_m_A*exp(-(V-beta_m_V0)/beta_m_K)",
        "mtau := 1.0/(q10*(alpha_m + beta_m))",
        "minf := alpha_m/(alpha_m + beta_m)",
        "alpha_h := alpha_h_A*exp(-(V-alpha_h_V0)/alpha_h_K)",
        "beta_h := beta_h_A/(exp(-(V-beta_h_V0)/beta_h_K) + 1.0)",
        "htau := 1.0/(q10*(alpha_h + beta_h))",
        "hinf := alpha_h/(alpha_h + beta_h)",
        "alpha_n := alpha_n_A*(V-alpha_n_V0)/(exp(-(V-alpha_n_V0)/alpha_n_K) - 1.0)",  # @IgnorePep8
        "beta_n := beta_n_A*exp(-(V-beta_n_V0)/beta_n_K)",
        "ntau := 1.0/(q10*(alpha_n + beta_n))",
        "ninf := alpha_n/(alpha_n + beta_n)",
        "gna := gnabar*m*m*m*h",
        "gk := gkbar*n*n*n*n",
        "ina := gna*(ena - V)",
        "ik := gk*(ek - V)",
        "il := gl*(el - V )"]

    hh_regime = al.Regime(
        "dn/dt = (ninf-n)/ntau",
        "dm/dt = (minf-m)/mtau",
        "dh/dt = (hinf-h)/htau",
        "dV/dt = (ina + ik + il + Isyn)/C",
        transitions=al.On("V > theta", do=al.SpikeOutputEvent())
    )

    state_variables = [
        al.StateVariable('V', un.voltage),
        al.StateVariable('m', un.dimensionless),
        al.StateVariable('n', un.dimensionless),
        al.StateVariable('h', un.dimensionless)]

    # the rest are not "parameters" but aliases, assigned vars, state vars,
    # indep vars, analog_analog_ports, etc.
    parameters = [
        al.Parameter('el', un.voltage),
        al.Parameter('C', un.capacitance),
        al.Parameter('ek', un.voltage),
        al.Parameter('ena', un.voltage),
        al.Parameter('gkbar', un.conductance),
        al.Parameter('gnabar', un.conductance),
        al.Parameter('theta', un.voltage),
        al.Parameter('gl', un.conductance),
        al.Parameter('celsius', un.temperature),
        al.Parameter('qfactor', un.temperature),
        al.Parameter('tendegrees', un.temperature),
        al.Parameter('alpha_m_A', un.dimensionless / (un.time * un.voltage)),
        al.Parameter('alpha_m_V0', un.voltage),
        al.Parameter('alpha_m_K', un.voltage),
        al.Parameter('beta_m_A', un.dimensionless / un.time),
        al.Parameter('beta_m_V0', un.voltage),
        al.Parameter('beta_m_K', un.voltage),
        al.Parameter('alpha_h_A', un.dimensionless / un.time),
        al.Parameter('alpha_h_V0', un.voltage),
        al.Parameter('alpha_h_K', un.voltage),
        al.Parameter('beta_h_A', un.dimensionless / un.time),
        al.Parameter('beta_h_V0', un.voltage),
        al.Parameter('beta_h_K', un.voltage),
        al.Parameter('alpha_n_A', un.dimensionless / (un.time * un.voltage)),
        al.Parameter('alpha_n_V0', un.voltage),
        al.Parameter('alpha_n_K', un.voltage),
        al.Parameter('beta_n_A', un.dimensionless / un.time),
        al.Parameter('beta_n_V0', un.voltage),
        al.Parameter('beta_n_K', un.voltage)]

    analog_ports = [al.AnalogSendPort("V", un.voltage),
                    al.AnalogReducePort("Isyn", un.current, operator="+")]

    dyn = al.Dynamics("HodgkinHuxley",
                      parameters=parameters,
                      state_variables=state_variables,
                      regimes=(hh_regime,),
                      aliases=aliases,
                      analog_ports=analog_ports)
    return dyn


if __name__ == '__main__':
    print etree.tostring(
        create_hodgkin_huxley().to_xml(),
        encoding="UTF-8", pretty_print=True, xml_declaration=True)
