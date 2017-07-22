from nineml import units as un, user as ul, abstraction as al


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
                      target_regime="sole",
                      do=[
                          al.StateAssignment(
                              'tlast_post',
                              '((w >= 0) ? ( tlast_post ) : ( t ))'),
                          al.StateAssignment(
                              'tlast_pre',
                              '((w >= 0) ? ( t ) : ( tlast_pre ))'),
                          al.StateAssignment(
                              'deltaw',
                              '((w >= 0) ? '
                              '( 0.0 ) : '
                              '( P*pow(wmax - wsyn, muLTP) * '
                              'exp(-interval/tauLTP) + deltaw ))'),
                          al.StateAssignment(
                              'interval',
                              '((w >= 0) ? ( -t + tlast_post ) : '
                              '( t - tlast_pre ))'),
                          al.StateAssignment(
                              'M',
                              '((w >= 0) ? ( M ) : '
                              '( M*exp((-t + tlast_post)/tauLTD) - aLTD ))'),
                          al.StateAssignment(
                              'P',
                              '((w >= 0) ? '
                              '( P*exp((-t + tlast_pre)/tauLTP) + aLTP ) : '
                              '( P ))'),
                          al.StateAssignment(
                              'wsyn', '((w >= 0) ? ( deltaw + wsyn ) : '
                              '( wsyn ))')]))])
    return dyn


def parameterise_stdp_guetig():

    comp = ul.DynamicsProperties(
        name='SampleAlpha',
        definition=create_stdp_guetig(),
        properties=[])
    return comp
