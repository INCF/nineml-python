import nineml.abstraction as al
from nineml import units as un


def get_component():
    iaf = al.dynamics.DynamicsClass(
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
                transitions=[al.On("t >= tspike + taurefrac",
                                   to="subthresholdregime")],
            )
        ],
        state_variables=[
            al.StateVariable('V', dimension=un.voltage),
            al.StateVariable('tspike', dimension=un.time),
        ],
        analog_ports=[al.AnalogSendPort("V", dimension=un.voltage),
                      al.AnalogReducePort("ISyn", dimension=un.current,
                                          operator="+"), ],

        event_ports=[al.EventSendPort('spikeoutput'), ],
        parameters=[al.Parameter('cm', dimension=un.capacitance),
                    al.Parameter('taurefrac', dimension=un.time),
                    al.Parameter('gl', dimension=un.conductance),
                    al.Parameter('vreset', dimension=un.voltage),
                    al.Parameter('vrest', dimension=un.voltage),
                    al.Parameter('vthresh', dimension=un.voltage)]
    )
    return iaf


if __name__ == '__main__':
    get_component()
