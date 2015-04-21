"""

"""

import nineml.abstraction_layer as al
from nineml.units import per_time, time, ms

model = al.Dynamics(
    name="Poisson",
    regimes=[
        al.Regime(
            name="default",
            transitions=al.On("t > t_next",
                              do=["t_next = t + one_ms * random.exponential(thousand_milliseconds * rate)",
                                  al.OutputEvent('spikeOutput')]))
    ],
    event_ports=[al.EventSendPort('spikeOutput')],
    state_variables=[al.StateVariable('t_next', dimension=time)],
    parameters=[al.Parameter('rate', dimension=per_time)],
    constants=[al.Constant('thousand_milliseconds', value=1000.0, units=ms),
               al.Constant('one_ms', value=1.0, units=ms)]
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
