from __future__ import division
from past.utils import old_div
from nineml import units as un
from nineml import abstraction as al, user as ul, Document
from nineml.xml import etree, E


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
        al.Parameter('d', old_div(un.voltage, un.time)),
        al.Parameter('C_m', un.capacitance),
        al.Parameter('alpha', old_div(un.dimensionless, (un.voltage * un.time))),
        al.Parameter('beta', un.per_time),
        al.Parameter('zeta', old_div(un.voltage, un.time))]

    state_variables = [
        al.StateVariable('V', un.voltage),
        al.StateVariable('U', old_div(un.voltage, un.time))]

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
            al.Parameter('b', old_div(un.conductance, (un.voltage ** 2))),
            al.Parameter('c', un.voltage),
            al.Parameter('k', old_div(un.conductance, un.voltage)),
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
    comp = ul.DynamicsProperties(
        name='SampleIzhikevich',
        definition=create_izhikevich(),
        properties=[ul.Property('a', 0.2 * un.per_ms),
                    ul.Property('b', 0.025 * un.per_ms),
                    ul.Property('c', -75 * un.mV),
                    ul.Property('d', 0.2 * un.mV / un.ms),
                    ul.Property('theta', -50 * un.mV),
                    ul.Property('alpha', 0.04 * un.unitless / (un.mV * un.ms)),
                    ul.Property('beta', 5 * un.per_ms),
                    ul.Property('zeta', 140.0 * un.mV / un.ms),
                    ul.Property('C_m', 1.0 * un.pF)],
        initial_values=[ul.Initial('V', -70 * un.mV),
                        ul.Initial('U', -1.625 * un.mV / un.ms)])
    return comp


def parameterise_izhikevich_fast_spiking(definition=None):
    if definition is None:
        definition = create_izhikevich_fast_spiking()
    comp = ul.DynamicsProperties(
        name='SampleIzhikevichFastSpiking',
        definition=create_izhikevich_fast_spiking(),
        properties=[ul.Property('a', 0.2 * un.per_ms),
                    ul.Property('b', 0.025 * un.nS / un.mV ** 2),
                    ul.Property('c', -45 * un.mV),
                    ul.Property('k', 1 * un.nS / un.mV),
                    ul.Property('Vpeak', 25 * un.mV),
                    ul.Property('Vb', -55 * un.mV),
                    ul.Property('Cm', 20 * un.pF),
                    ul.Property('Vr', -55 * un.mV),
                    ul.Property('Vt', -40 * un.mV)],
        initial_values=[ul.Initial('V', -70 * un.mV),
                        ul.Initial('U', -1.625 * un.mV / un.ms)])
    return comp
