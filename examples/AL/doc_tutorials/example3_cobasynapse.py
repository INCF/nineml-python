import nineml.abstraction as al

cond_decay = al.Regime(name='default',
                       time_derivatives=["dg/dt = -g/tau"],
                       transitions=[al.On(al.InputEvent('spikeinput'), do="g = g + q")]
                       )


coba_syn = al.ComponentClass(
    name="CoBaSynapse",
    dynamics=al.DynamicsBlock(
        regimes=[cond_decay],
        aliases=["I := g*(E-V)"],
    ),
    analog_ports=[al.RecvPort("V"), al.SendPort("I")]
)
