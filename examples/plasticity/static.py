from __future__ import print_function
from nineml import units as un, user as ul, abstraction as al, Document
from nineml.xml import etree, E


def create_static():
    dyn = al.Dynamics(
        name="Static",
        aliases=["fixed_weight := weight"],
        regimes=[
            al.Regime(name="default")],
        analog_ports=[al.AnalogSendPort("fixed_weight", dimension=un.current)],
        parameters=[al.Parameter('weight', dimension=un.current)])
    return dyn


def parameterise_static():

    comp = ul.DynamicsProperties(
        name='SampleAlpha',
        definition=create_static(),
        properties=[ul.Property('weight', 10.0 * un.nA)])
    return comp


if __name__ == '__main__':
    import argparse
    try:
        import ninemlcatalog
        catalog_path = 'plasticity/Static'
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
        print(etree.tostring(
            E.NineML(
                create_static().to_xml(document),
                parameterise_static().to_xml(document)),
            encoding="UTF-8", pretty_print=True, xml_declaration=True))
    elif args.mode == 'compare':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        local_version = create_static()
        catalog_version = ninemlcatalog.load(catalog_path,
                                               local_version.name)
        mismatch = local_version.find_mismatch(catalog_version)
        if mismatch:
            print ("Local version differs from catalog version:\n{}"
                   .format(mismatch))
        else:
            print("Local version matches catalog version")
    elif args.mode == 'save':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        dynamics = create_static()
        ninemlcatalog.save(dynamics, catalog_path, dynamics.name)
        params = parameterise_static(
            ninemlcatalog.load(catalog_path, dynamics.name))
        ninemlcatalog.save(params, catalog_path, params.name)
        print("Saved '{}' and '{}' to catalog".format(dynamics.name,
                                                      params.name))
