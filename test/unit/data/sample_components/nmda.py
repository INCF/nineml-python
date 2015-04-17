
import nineml.abstraction as al


def get_component():
    inter_event_regime = al.Regime(
        name="intereventregime",
        time_derivatives=["dA/dt = -A/taur", "dB/dt = -B/taud"],
        transitions=[al.On('spikeinput',
                           do=["A = A + weight*factor",
                               "B = B + weight*factor"])]
    )

    nmda = al.Dynamics(
        name="NMDAPSR",
        aliases=[
            "taupeak := taur*taud/(taud - taur)*log(taud/taur)",
            "factor := 1/(exp(-taupeak/taud) - exp(-taupeak/taur))",
            "gB := 1/(1 + mgconc*exp(-1*gamma*V)/beta)",
            "g := gB*gmax*(B-A)",
            "I := g * df",
            "df := (E-V)",
        ],
        state_variables=[al.StateVariable(o) for o in ('A', 'B')],
        regimes=[inter_event_regime],
        analog_ports=[al.AnalogReceivePort("V"), al.AnalogSendPort("I"), ],
        event_ports=[al.AnalogReceivePort('spikeinput')],
        parameters=['taur', 'taud', 'gmax', 'mgconc', 'gamma', 'beta', 'E',
                    'weight'])

    return nmda
