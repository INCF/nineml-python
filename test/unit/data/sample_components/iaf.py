import nineml.abstraction_layer as al


def get_component():
    iaf = al.dynamics.Dynamics(
        name="iaf",
        regimes=[
            al.Regime(
                name="subthresholdregime",
                time_derivatives=["dV/dt = ( gl*( vrest - V ) + ISyn)/(cm)"],
                transitions=al.On("V > vthresh",
                                  do=["tspike = t",
                                      "V = vreset",
                                      al.OutputEvent('spikeoutput')],
                                  to="refractoryregime"),
            ),

            al.Regime(
                name="refractoryregime",
                time_derivatives=["dV/dt = 0"],
                transitions=[al.On("t >= tspike + taurefrac",
                                   to="subthresholdregime")],
            )
        ],
        state_variables=[
            al.StateVariable('V'),
            al.StateVariable('tspike'),
        ],
        analog_ports=[al.AnalogSendPort("V"),
                      al.AnalogReducePort("ISyn", operator="+"), ],

        event_ports=[al.EventSendPort('spikeoutput'), ],
        parameters=['cm', 'taurefrac', 'gl', 'vreset', 'vrest', 'vthresh']
    )
    return iaf

if __name__ == '__main__':
    get_component()
