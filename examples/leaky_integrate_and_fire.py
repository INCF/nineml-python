from nineml.abstraction import (
    Dynamics, Regime, OutputEvent, On, StateAssignment, StateVariable,
    Parameter, AnalogReducePort)
from nineml import units as un
from lxml import etree


def create_leaky_integrate_and_fire():
    dyn = Dynamics(
        name='leakyIAF',
        regimes=[
            Regime('dv/dt = (g * (v_rest - v) + i_synaptic) /cm',
                   transitions=[On('v > v_threshold',
                                   do=[OutputEvent('output_spike'),
                                       StateAssignment('t_spike', 't'),
                                       StateAssignment('v', 'v_reset')],
                                   to='refractory')],
                   name='subthreshold'),
            Regime(transitions=[On('t > t_spike + t_refractory',
                                   to='subthreshold')],
                   name='refractory')],
        state_variables=[StateVariable('v', dimension=un.voltage),
                         StateVariable('t_spike', dimension=un.time)],
        parameters=[Parameter('cm', un.capacitance),
                    Parameter('t_refractory', un.time),
                    Parameter('v_rest', un.voltage),
                    Parameter('v_reset', un.voltage),
                    Parameter('v_threshold', un.voltage),
                    Parameter('g', un.conductance)],
        analog_ports=[AnalogReducePort('i_synaptic', un.current, operator='+')])

    return dyn

if __name__ == '__main__':
    print etree.tostring(
        create_leaky_integrate_and_fire().to_xml(),
        encoding="UTF-8", pretty_print=True, xml_declaration=True)
