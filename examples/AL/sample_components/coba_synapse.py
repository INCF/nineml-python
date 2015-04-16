import nineml.abstraction_layer as al
import nineml.units as un


def get_component():
    coba = al.dynamics.DynamicsClass(
        name="CobaSyn",
        aliases=["I:=g*(vrev-V)", ],
        regimes=[
            al.Regime(
                name="cobadefaultregime",
                time_derivatives=["dg/dt = -g/tau", ],
                transitions=al.On('spikeinput', do=["g=g+q"]),
            )
        ],
        state_variables=[al.StateVariable('g', dimension=un.conductance)],
        analog_ports=[al.AnalogReceivePort("V", dimension=un.voltage),
                      al.AnalogSendPort("I", dimension=un.current)],
        parameters=[al.Parameter('tau', dimension=un.time),
                    al.Parameter('q', dimension=un.conductance),
                    al.Parameter('vrev', dimension=un.voltage)]
    )
    return coba

if __name__ == '__main__':
    get_component()
