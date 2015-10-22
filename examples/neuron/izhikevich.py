from nineml import units as un
from nineml import abstraction as al, user as ul  # @Reimport
from nineml.xmlns import etree, E


def create_izhikevich():
    subthreshold_regime = al.Regime(
        name="subthreshold_regime",
        time_derivatives=[
            "dV/dt = alpha*V*V + beta*V + zeta - U + Isyn / C_m",
            "dU/dt = a*(b*V - U)", ],

        transitions=[al.On("V > theta",
                           do=["V = c",
                               "U =  U+ d",
                               al.OutputEvent('spike')],
                           to='subthreshold_regime')]
    )

    ports = [al.AnalogSendPort("V", un.voltage),
             al.AnalogReducePort("Isyn", un.current, operator="+")]

    parameters = [
        al.Parameter('theta', un.voltage),
        al.Parameter('a', un.per_time),
        al.Parameter('b', un.per_time),
        al.Parameter('c', un.voltage),
        al.Parameter('d', un.voltage / un.time),
        al.Parameter('C_m', un.capacitance),
        al.Parameter('alpha', un.dimensionless / (un.voltage * un.time)),
        al.Parameter('beta', un.per_time),
        al.Parameter('zeta', un.voltage / un.time)]

    state_variables = [
        al.StateVariable('V', un.voltage),
        al.StateVariable('U', un.voltage / un.time)]

    c1 = al.Dynamics(
        name="Izhikevich",
        parameters=parameters,
        state_variables=state_variables,
        regimes=[subthreshold_regime],
        analog_ports=ports

    )
    return c1


def create_izhikevich_fast_spiking():
    """
    Load Fast spiking Izhikevich XML definition from file and parse into
    Abstraction Layer of Python API.
    """
    izhi_fs = al.Dynamics(
        name='IzhikevichFastSpiking',
        parameters=[
            al.Parameter('a', un.per_time),
            al.Parameter('b', un.conductance / (un.voltage ** 2)),
            al.Parameter('c', un.voltage),
            al.Parameter('k', un.conductance / un.voltage),
            al.Parameter('Vr', un.voltage),
            al.Parameter('Vt', un.voltage),
            al.Parameter('Vb', un.voltage),
            al.Parameter('Vpeak', un.voltage),
            al.Parameter('Cm', un.capacitance)],
        analog_ports=[
            al.AnalogReducePort('iSyn', un.current, operator="+"),
            al.AnalogSendPort('U', un.current),
            al.AnalogSendPort('V', un.voltage)],
        event_ports=[
            al.EventSendPort("spikeOutput")],
        state_variables=[
            al.StateVariable('V', un.voltage),
            al.StateVariable('U', un.current)],
        regimes=[
            al.Regime(
                'dU/dt = a * (b * pow(V - Vb, 3) - U)',
                'dV/dt = V_deriv',
                transitions=[
                    al.On('V > Vpeak',
                          do=['V = c', al.OutputEvent('spikeOutput')],
                          to='subthreshold')],
                name="subthreshold"),
            al.Regime(
                'dU/dt = - U * a',
                'dV/dt = V_deriv',
                transitions=[al.On('V > Vb', to="subthreshold")],
                name="subVb")],
        aliases=["V_deriv := (k * (V - Vr) * (V - Vt) - U + iSyn) / Cm"])  # @IgnorePep8
    return izhi_fs


def parameterise_izhikevich(definition=None):
    if definition is None:
        definition = create_izhikevich()
    comp = ul.DynamicsComponent(
        name='SampleIzhikevich',
        definition=create_izhikevich(),
        properties=[ul.Property('a', 0.2, un.per_ms),
                    ul.Property('b', 0.025, un.per_ms),
                    ul.Property('c', -75, un.mV),
                    ul.Property('d', 0.2, un.mV / un.ms),
                    ul.Property('theta', -50, un.mV),
                    ul.Property('alpha', 0.04, un.unitless / (un.mV * un.ms)),
                    ul.Property('beta', 5, un.per_ms),
                    ul.Property('zeta', 140.0, un.mV / un.ms),
                    ul.Property('C_m', 1.0, un.pF)],
        initial_values=[ul.Initial('V', -70, un.mV),
                        ul.Initial('U', -1.625, un.mV / un.ms)])
    return comp


def parameterise_izhikevich_fast_spiking(definition=None):
    if definition is None:
        definition = create_izhikevich_fast_spiking()
    comp = ul.DynamicsComponent(
        name='SampleIzhikevichFastSpiking',
        definition=create_izhikevich_fast_spiking(),
        properties=[ul.Property('a', 0.2, un.per_ms),
                    ul.Property('b', 0.025, un.nS / un.mV ** 2),
                    ul.Property('c', -45, un.mV),
                    ul.Property('k', 1, un.nS / un.mV),
                    ul.Property('Vpeak', 25, un.mV),
                    ul.Property('Vb', -55, un.mV),
                    ul.Property('Cm', 20, un.pF),
                    ul.Property('Vr', -55, un.mV),
                    ul.Property('Vt', -40, un.mV)],
        initial_values=[ul.Initial('V', -70, un.mV),
                        ul.Initial('U', -1.625, un.mV / un.ms)])
    return comp


if __name__ == '__main__':
    import argparse
    try:
        import ninemlcatalog
        catalog_path = 'neuron/Izhikevich'
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
        print etree.tostring(
            E.NineML(
                create_izhikevich().to_xml(),
                parameterise_izhikevich().to_xml(),
                create_izhikevich_fast_spiking().to_xml(),
                parameterise_izhikevich_fast_spiking().to_xml()),
            encoding="UTF-8", pretty_print=True, xml_declaration=True)
    elif args.mode == 'compare':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        local_version = create_izhikevich()
        catalog_version = ninemlcatalog.load(catalog_path,
                                               local_version.name)
        mismatch = local_version.find_mismatch(catalog_version)
        if mismatch:
            print ("Local version of Izhikevich model differs from catalog "
                   "version:\n{}".format(mismatch))
        else:
            print "Local version of Izhikevich model matches catalog version"
        local_version = create_izhikevich_fast_spiking()
        catalog_version = ninemlcatalog.load(catalog_path,
                                               local_version.name)
        mismatch = local_version.find_mismatch(catalog_version)
        if mismatch:
            print ("Local version of Izhikevich Fast Spiking model differs "
                   "from catalog version:\n{}".format(mismatch))
        else:
            print ("Local version of Izhikevich Fast Spiking model matches "
                   "catalog version")
    elif args.mode == 'save':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        dynamics = create_izhikevich()
        ninemlcatalog.save(dynamics, catalog_path, dynamics.name)
        params = parameterise_izhikevich(
            ninemlcatalog.load(catalog_path, dynamics.name))
        ninemlcatalog.save(params, catalog_path, params.name)
        print "Saved '{}' and '{}' to catalog".format(dynamics.name,
                                                      params.name)
        dynamics = create_izhikevich_fast_spiking()
        ninemlcatalog.save(dynamics, catalog_path, dynamics.name)
        params = parameterise_izhikevich_fast_spiking(
            ninemlcatalog.load(catalog_path, dynamics.name))
        ninemlcatalog.save(params, catalog_path, params.name)
        print "Saved '{}' and '{}' to catalog".format(dynamics.name,
                                                      params.name)
