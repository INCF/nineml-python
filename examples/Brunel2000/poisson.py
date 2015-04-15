"""

"""

import nineml.abstraction_layer as al
from nineml.units import time, per_time

model = al.DynamicsClass(
    name="Poisson",
    regimes=[
        al.Regime(
            name="default",
            transitions=al.On("t > t_next",
                              do=["t_next = t + random.exponential(1000/rate)",
                                  al.OutputEvent('spikeOutput')]))
    ],
    event_ports=[al.EventSendPort('spikeOutput')],
    state_variables=[al.StateVariable('t_next', dimension=time)],
    parameters=[al.Parameter('rate', dimension=per_time),]
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
