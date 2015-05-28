import nineml.abstraction as al
r1 = al.Regime(
    name="sub-threshold-regime",
    time_derivatives=["dV/dt = (-gL*(V-vL) + I)/C", ],
    transitions=[al.On("V>Vth",
                       do=["tspike = t",
                           "V = V_reset",
                           al.OutputEvent('spike')],
                 to="refractory-regime"), ],
)

r2 = al.Regime(name="refractory-regime",
               transitions=[al.On("t >= tspike + trefractory",
                                  to="sub-threshold-regime"), ],
               )

leaky_iaf = al.ComponentClass("LeakyIAF",
                              dynamicsblock=al.DynamicsBlock(
                              regimes=[r1, r2],
                              state_variables=['V', 'tspike'],

                              ),
                              analog_ports=[al.AnalogPort("I", mode='recv')],
                              parameters=['C', 'V_reset', 'Vth', 'gL', 't', 'trefractory', 'vL'],
                              )


leaky_iaf.write("leaky_iaf.xml")
