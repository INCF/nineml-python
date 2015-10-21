from nineml import units as un
from nineml import abstraction as al  # @Reimport
from lxml import etree


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
        name='IzhikevichFS',
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
            al.AnalogReducePort('iExt', un.current, operator="+"),
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
        aliases=["V_deriv := (k * (V - Vr) * (V - Vt) - U + iExt + iSyn) / Cm"])  # @IgnorePep8
    return izhi_fs


if __name__ == '__main__':
    print etree.tostring(
        create_izhikevich().to_xml(),
        encoding="UTF-8", pretty_print=True, xml_declaration=True)
