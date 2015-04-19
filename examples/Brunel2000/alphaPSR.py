import nineml.abstraction as al
from nineml.units import current, time

model = al.Dynamics(
    name="AlphaPSR",
    aliases=["Isyn := A"],
    regimes=[
        al.Regime(
            name="default",
            time_derivatives=[
                "dA/dt = (B - A)/tau_syn",  # TGC 4/15 changed from "B - A/tau_syn" as dimensions didn't add up @IgnorePep8
                "dB/dt = -B/tau_syn"],
            transitions=al.On('spike',
                              do=["B = B + weight"]),
        )
    ],
    state_variables=[
        al.StateVariable('A', dimension=current),
        al.StateVariable('B', dimension=current),
    ],
    analog_ports=[al.AnalogSendPort("Isyn", dimension=current),
                  al.AnalogSendPort("A", dimension=current),
                  al.AnalogSendPort("B", dimension=current),
                  al.AnalogReceivePort("weight", dimension=current)],
    parameters=[al.Parameter('tau_syn', dimension=time)]
)


if __name__ == "__main__":
    import nineml
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    nineml.write(model, filename)
