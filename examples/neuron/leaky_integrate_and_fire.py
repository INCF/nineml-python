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
