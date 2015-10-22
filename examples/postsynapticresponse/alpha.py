from nineml import units as un, user as ul, abstraction as al
from nineml.xmlns import etree, E


def create_alpha():
    dyn = al.Dynamics(
        name="Alpha",
        aliases=["Isyn := A"],
        regimes=[
            al.Regime(
                name="default",
                time_derivatives=[
                    "dA/dt = (B - A)/tau",  # TGC 4/15 changed from "B - A/tau_syn" as dimensions didn't add up @IgnorePep8
                    "dB/dt = -B/tau"],
                transitions=al.On('spike',
                                  do=["B = B + q"]))],
        state_variables=[
            al.StateVariable('A', dimension=un.current),
            al.StateVariable('B', dimension=un.current),
        ],
        analog_ports=[al.AnalogSendPort("Isyn", dimension=un.current),
                      al.AnalogSendPort("A", dimension=un.current),
                      al.AnalogSendPort("B", dimension=un.current),
                      al.AnalogReceivePort("q", dimension=un.current)],
        parameters=[al.Parameter('tau', dimension=un.time)])
    return dyn


def parameterise_alpha():

    comp = ul.DynamicsComponent(
        name='SampleAlpha',
        definition=create_alpha(),
        properties=[ul.Property('tau', 20.0, un.ms)],
        initial_values=[ul.Initial('a', 0.0, un.pA),
                        ul.Initial('b', 0.0, un.pA)])
    return comp


if __name__ == '__main__':
    import argparse
    try:
        import ninemlcatalog
        catalog_path = 'postsynapticresponse/Alpha'
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
                create_alpha().to_xml(),
                parameterise_alpha().to_xml()),
            encoding="UTF-8", pretty_print=True, xml_declaration=True)
    elif args.mode == 'compare':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        local_version = create_alpha()
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
        dynamics = create_alpha()
        ninemlcatalog.save(dynamics, catalog_path, dynamics.name)
        params = parameterise_alpha(
            ninemlcatalog.load(catalog_path, dynamics.name))
        ninemlcatalog.save(params, catalog_path, params.name)
        print "Saved '{}' and '{}' to catalog".format(dynamics.name,
                                                      params.name)