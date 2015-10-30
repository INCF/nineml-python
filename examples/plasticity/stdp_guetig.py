from nineml import units as un, user as ul, abstraction as al, Document
from nineml.xml import etree, E


def create_stdp_guetig():
    dyn = al.Dynamics(
        name="StdpGuetig",
        parameters=[
            al.Parameter(name='tauLTP', dimension=un.time),
            al.Parameter(name='aLTD', dimension=un.dimensionless),
            al.Parameter(name='wmax', dimension=un.dimensionless),
            al.Parameter(name='muLTP', dimension=un.dimensionless),
            al.Parameter(name='tauLTD', dimension=un.time),
            al.Parameter(name='aLTP', dimension=un.dimensionless)],
        analog_ports=[
            al.AnalogReceivePort(dimension=un.dimensionless, name="w"),
            al.AnalogSendPort(dimension=un.dimensionless, name="wsyn")],
        event_ports=[
            al.EventReceivePort(name="incoming_spike")],
        state_variables=[
            al.StateVariable(name='tlast_post', dimension=un.time),
            al.StateVariable(name='tlast_pre', dimension=un.time),
            al.StateVariable(name='deltaw', dimension=un.dimensionless),
            al.StateVariable(name='interval', dimension=un.time),
            al.StateVariable(name='M', dimension=un.dimensionless),
            al.StateVariable(name='P', dimension=un.dimensionless),
            al.StateVariable(name='wsyn', dimension=un.dimensionless)],
        regimes=[
            al.Regime(
                name="sole",
                al.On('incoming_spike',
                      target_regime="regime_0",
                      do=[
                          al.StateAssignment(
                              'tlast_post',
                              '((w &gt;= 0) ? ( tlast_post ) : ( t ))'),
                          al.StateAssignment(
                              'tlast_pre',
                              '((w &gt;= 0) ? ( t ) : ( tlast_pre ))'),
                          al.StateAssignment(
                              'deltaw',
                              '((w &gt;= 0) ? '
                              '( 0.0 ) : '
                              '( P*pow(wmax - wsyn, muLTP) * '
                              'exp(-interval/tauLTP) + deltaw ))'),
                          al.StateAssignment(
                              'interval',
                              '((w &gt;= 0) ? ( -t + tlast_post ) : '
                              '( t - tlast_pre ))'),
                          al.StateAssignment(
                              'M',
                              '((w &gt;= 0) ? ( M ) : '
                              '( M*exp((-t + tlast_post)/tauLTD) - aLTD ))'),
                          al.StateAssignment(
                              'P',
                              '((w &gt;= 0) ? '
                              '( P*exp((-t + tlast_pre)/tauLTP) + aLTP ) : '
                              '( P ))'),
                          al.StateAssignment(
                              'wsyn', '((w &gt;= 0) ? ( deltaw + wsyn ) : '
                              '( wsyn ))')]))])
    return dyn


def parameterise_stdp_guetig():

    comp = ul.DynamicsProperties(
        name='SampleAlpha',
        definition=create_stdp_guetig(),
        properties=[])
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
        print etree.tostring(
            E.NineML(
                create_stdp_guetig().to_xml(document),
                parameterise_stdp_guetig().to_xml(document)),
            encoding="UTF-8", pretty_print=True, xml_declaration=True)
    elif args.mode == 'compare':
        if ninemlcatalog is None:
            raise Exception(
                "NineML catalog is not installed")
        local_version = create_stdp_guetig()
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
        dynamics = create_stdp_guetig()
        ninemlcatalog.save(dynamics, catalog_path, dynamics.name)
        params = parameterise_stdp_guetig(
            ninemlcatalog.load(catalog_path, dynamics.name))
        ninemlcatalog.save(params, catalog_path, params.name)
        print "Saved '{}' and '{}' to catalog".format(dynamics.name,
                                                      params.name)
