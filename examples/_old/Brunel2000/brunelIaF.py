"""

"""

import nineml.abstraction as al
from nineml.units import voltage, time, resistance, current

model = al.Dynamics(
    name="BrunelIaF",
    regimes=[
        al.Regime(
            name="subthresholdRegime",
            time_derivatives=["dV/dt = (-V + R*Isyn)/tau"],
            transitions=al.On("V > theta",
                              do=["t_rpend = t + tau_rp",
                                  "V = Vreset",
                                  al.OutputEvent('spikeOutput')],
                              to="refractoryRegime"),
        ),
        al.Regime(
            name="refractoryRegime",
            transitions=[al.On("t > t_rpend",
                               #do=[al.OutputEvent('refractoryEnd')],
                               to="subthresholdRegime")],
        )
    ],
    state_variables=[
        al.StateVariable('V', dimension=voltage),
        al.StateVariable('t_rpend', dimension=time)],
    analog_ports=[
        al.AnalogSendPort("V", dimension=voltage),
        al.AnalogSendPort("t_rpend", dimension=time),
        al.AnalogReducePort("Isyn", operator="+", dimension=current)],
    event_ports=[
        al.EventSendPort('spikeOutput'),
        ],
    parameters=[
        al.Parameter('tau', time),
        al.Parameter('theta', voltage),
        al.Parameter('tau_rp', time),
        al.Parameter('Vreset', voltage),
        al.Parameter('R', resistance)]
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
