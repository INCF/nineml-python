from nineml import abstraction as al, user as ul, Document
from nineml import units as un
from nineml.xml import E, etree


def create_hodgkin_huxley():
    """A Hodgkin-Huxley single neuron model.
    Written by Andrew Davison.
    See http://phobos.incf.ki.se/src_rst/
              examples/examples_al_python.html#example-hh
    """
    aliases = [
        "q10 := 3.0**((celsius - qfactor)/tendegrees)",  # temperature correction factor @IgnorePep8
        "m_alpha := m_alpha_A*(V-m_alpha_V0)/(exp(-(V-m_alpha_V0)/m_alpha_K) - 1.0)",  # @IgnorePep8
        "m_beta := m_beta_A*exp(-(V-m_beta_V0)/m_beta_K)",
        "mtau := 1.0/(q10*(m_alpha + m_beta))",
        "minf := m_alpha/(m_alpha + m_beta)",
        "h_alpha := h_alpha_A*exp(-(V-h_alpha_V0)/h_alpha_K)",
        "h_beta := h_beta_A/(exp(-(V-h_beta_V0)/h_beta_K) + 1.0)",
        "htau := 1.0/(q10*(h_alpha + h_beta))",
        "hinf := h_alpha/(h_alpha + h_beta)",
        "n_alpha := n_alpha_A*(V-n_alpha_V0)/(exp(-(V-n_alpha_V0)/n_alpha_K) - 1.0)",  # @IgnorePep8
        "n_beta := n_beta_A*exp(-(V-n_beta_V0)/n_beta_K)",
        "ntau := 1.0/(q10*(n_alpha + n_beta))",
        "ninf := n_alpha/(n_alpha + n_beta)",
        "gna := gnabar*m*m*m*h",
        "gk := gkbar*n*n*n*n",
        "ina := gna*(ena - V)",
        "ik := gk*(ek - V)",
        "il := gl*(el - V )"]

    hh_regime = al.Regime(
        "dn/dt = (ninf-n)/ntau",
        "dm/dt = (minf-m)/mtau",
        "dh/dt = (hinf-h)/htau",
        "dV/dt = (ina + ik + il + isyn)/C",
        transitions=al.On("V > v_threshold", do=al.SpikeOutputEvent())
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
        al.Parameter('v_threshold', un.voltage),
        al.Parameter('gl', un.conductance),
        al.Parameter('celsius', un.temperature),
        al.Parameter('qfactor', un.temperature),
        al.Parameter('tendegrees', un.temperature),
        al.Parameter('m_alpha_A', un.dimensionless / (un.time * un.voltage)),
        al.Parameter('m_alpha_V0', un.voltage),
        al.Parameter('m_alpha_K', un.voltage),
        al.Parameter('m_beta_A', un.dimensionless / un.time),
        al.Parameter('m_beta_V0', un.voltage),
        al.Parameter('m_beta_K', un.voltage),
        al.Parameter('h_alpha_A', un.dimensionless / un.time),
        al.Parameter('h_alpha_V0', un.voltage),
        al.Parameter('h_alpha_K', un.voltage),
        al.Parameter('h_beta_A', un.dimensionless / un.time),
        al.Parameter('h_beta_V0', un.voltage),
        al.Parameter('h_beta_K', un.voltage),
        al.Parameter('n_alpha_A', un.dimensionless / (un.time * un.voltage)),
        al.Parameter('n_alpha_V0', un.voltage),
        al.Parameter('n_alpha_K', un.voltage),
        al.Parameter('n_beta_A', un.dimensionless / un.time),
        al.Parameter('n_beta_V0', un.voltage),
        al.Parameter('n_beta_K', un.voltage)]

    analog_ports = [al.AnalogSendPort("V", un.voltage),
                    al.AnalogReducePort("isyn", un.current, operator="+")]

    dyn = al.Dynamics("HodgkinHuxley",
                      parameters=parameters,
                      state_variables=state_variables,
                      regimes=(hh_regime,),
                      aliases=aliases,
                      analog_ports=analog_ports)
    return dyn


def parameterise_hodgkin_huxley(definition=None):
    if definition is None:
        definition = create_hodgkin_huxley()
    comp = ul.DynamicsProperties(
        name='SampleHodgkinHuxley',
        definition=create_hodgkin_huxley(),
        properties=[ul.Property('C', 1.0 * un.pF),
                    ul.Property('celsius', 20.0 * un.degC),
                    ul.Property('ek', -90 * un.mV),
                    ul.Property('el', -65 * un.mV),
                    ul.Property('ena', 80 * un.mV),
                    ul.Property('gkbar', 30.0 * un.nS),
                    ul.Property('gl', 0.3 * un.nS),
                    ul.Property('gnabar', 130.0 * un.nS),
                    ul.Property('v_threshold', -40.0 * un.mV),
                    ul.Property('qfactor', 6.3 * un.degC),
                    ul.Property('tendegrees', 10.0 * un.degC),
                    ul.Property('m_alpha_A', -0.1,
                                un.unitless / (un.ms * un.mV)),
                    ul.Property('m_alpha_V0', -40.0 * un.mV),
                    ul.Property('m_alpha_K', 10.0 * un.mV),
                    ul.Property('m_beta_A', 4.0 * un.per_ms),
                    ul.Property('m_beta_V0', -65.0 * un.mV),
                    ul.Property('m_beta_K', 18.0 * un.mV),
                    ul.Property('h_alpha_A', 0.07 * un.per_ms),
                    ul.Property('h_alpha_V0', -65.0 * un.mV),
                    ul.Property('h_alpha_K', 20.0 * un.mV),
                    ul.Property('h_beta_A', 1.0 * un.per_ms),
                    ul.Property('h_beta_V0', -35.0 * un.mV),
                    ul.Property('h_beta_K', 10.0 * un.mV),
                    ul.Property('n_alpha_A', -0.01,
                                un.unitless / (un.ms * un.mV)),
                    ul.Property('n_alpha_V0', -55.0 * un.mV),
                    ul.Property('n_alpha_K', 10.0 * un.mV),
                    ul.Property('n_beta_A', 0.125 * un.per_ms),
                    ul.Property('n_beta_V0', -65.0 * un.mV),
                    ul.Property('n_beta_K', 80.0 * un.mV)],
        initial_values=[ul.Initial('V', -70 * un.mV),
                        ul.Initial('m', 0.1),
                        ul.Initial('n', 0),
                        ul.Initial('h', 0.9)])
    return comp


if __name__ == '__main__':
    import argparse
    try:
        import ninemlcatalog
        catalog_path = 'neuron/HodgkinHuxley'
    except ImportError:
        ninemlcatalog = None
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='print',
                        help=("The mode to run this script, can be 'print', "
                              "'compare' or 'save', which correspond to "
                              "printing the models, comparing the models with "
                              "the version in the catalog, or overwriting the "
                              "version in the catalog with this version "
                              "respectively"))
    args = parser.parse_args()

    if args.mode == 'print':
        document = Document()
        print etree.tostring(
            E.NineML(
                create_hodgkin_huxley().to_xml(document),
                parameterise_hodgkin_huxley().to_xml(document)),
            encoding="UTF-8", pretty_print=True, xml_declaration=True)
    elif args.mode == 'compare':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        local_version = create_hodgkin_huxley()
        catalog_version = ninemlcatalog.load(catalog_path,
                                               local_version.name)
        mismatch = local_version.find_mismatch(catalog_version)
        if mismatch:
            print ("Local version differs from catalog version:\n{}"
                   .format(mismatch))
        else:
            print "Local version matches catalog version"
    elif args.mode == 'save':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        dynamics = create_hodgkin_huxley()
        ninemlcatalog.save(dynamics, catalog_path, dynamics.name)
        params = parameterise_hodgkin_huxley(
            ninemlcatalog.load(catalog_path, dynamics.name))
        ninemlcatalog.save(params, catalog_path, params.name)
        print "Saved '{}' and '{}' to catalog".format(dynamics.name,
                                                      params.name)
