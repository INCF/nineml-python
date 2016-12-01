from nineml import abstraction as al, user as ul, Document
from nineml import units as un
from nineml.xml import etree, E


def create_leaky_integrate_and_fire():
    dyn = al.Dynamics(
        name='LeakyIntegrateAndFire',
        regimes=[
            al.Regime('dv/dt = (i_synaptic*R - v)/tau',
                      transitions=[al.On('v > v_threshold',
                                         do=[al.OutputEvent('spike_output'),
                                             al.StateAssignment(
                                                 'refractory_end',
                                                 't + refractory_period'),
                                             al.StateAssignment('v',
                                                                'v_reset')],
                                         to='refractory')],
                      name='subthreshold'),
            al.Regime(transitions=[al.On('t > refractory_end',
                                   to='subthreshold')],
                      name='refractory')],
        state_variables=[al.StateVariable('v', dimension=un.voltage),
                         al.StateVariable('refractory_end',
                                          dimension=un.time)],
        parameters=[al.Parameter('R', un.resistance),
                    al.Parameter('refractory_period', un.time),
                    al.Parameter('v_reset', un.voltage),
                    al.Parameter('v_threshold', un.voltage),
                    al.Parameter('tau', un.time)],
        analog_ports=[al.AnalogReducePort('i_synaptic', un.current,
                                          operator='+'),
                      al.AnalogSendPort('refractory_end', un.time),
                      al.AnalogSendPort('v', un.voltage)])

    return dyn


def parameterise_leaky_integrate_and_fire(definition=None):
    if definition is None:
        definition = create_leaky_integrate_and_fire()
    comp = ul.DynamicsProperties(
        name='SampleLeakyIntegrateAndFire',
        definition=create_leaky_integrate_and_fire(),
        properties=[ul.Property('tau', 20.0 * un.ms),
                    ul.Property('v_threshold', 20.0 * un.mV),
                    ul.Property('refractory_period', 2.0 * un.ms),
                    ul.Property('v_reset', 10.0 * un.mV),
                    ul.Property('R', 1.5 * un.Mohm)],
        initial_values=[ul.Initial('V', -70 * un.mV)])
    return comp


if __name__ == '__main__':
    import argparse
    try:
        import ninemlcatalog
        catalog_path = 'neuron/LeakyIntegrateAndFire'
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
                create_leaky_integrate_and_fire().to_xml(document),
                parameterise_leaky_integrate_and_fire().to_xml(document)),
            encoding="UTF-8", pretty_print=True, xml_declaration=True)
    elif args.mode == 'compare':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        local_version = create_leaky_integrate_and_fire()
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
        dynamics = create_leaky_integrate_and_fire()
        ninemlcatalog.save(dynamics, catalog_path, dynamics.name)
        params = parameterise_leaky_integrate_and_fire(
            ninemlcatalog.load(catalog_path, dynamics.name))
        ninemlcatalog.save(params, catalog_path, params.name)
        print "Saved '{}' and '{}' to catalog".format(dynamics.name,
                                                      params.name)

