from nineml import units as un, user as ul, abstraction as al, Document
from nineml.xml import etree, E


def create_alpha():
    dyn = al.Dynamics(
        name="Alpha",
        aliases=["Isyn := A"],
        regimes=[
            al.Regime(
                name="default",
                time_derivatives=[
                    "dA/dt = (B - A)/tau",  # TGC 4/15 changed from "B - A/tau_syn" as dimensions didn't add up @IgnorePep8
                    "dB/dt = -B/tau"],
                transitions=al.On('spike',
                                  do=["B = B + q"]))],
        state_variables=[
            al.StateVariable('A', dimension=un.current),
            al.StateVariable('B', dimension=un.current),
        ],
        analog_ports=[al.AnalogSendPort("Isyn", dimension=un.current),
                      al.AnalogSendPort("A", dimension=un.current),
                      al.AnalogSendPort("B", dimension=un.current),
                      al.AnalogReceivePort("q", dimension=un.current)],
        parameters=[al.Parameter('tau', dimension=un.time)])
    return dyn


def parameterise_alpha():

    comp = ul.DynamicsProperties(
        name='SampleAlpha',
        definition=create_alpha(),
        properties=[ul.Property('tau', 20.0 * un.ms)],
        initial_values=[ul.Initial('a', 0.0 * un.pA),
                        ul.Initial('b', 0.0 * un.pA)])
    return comp
