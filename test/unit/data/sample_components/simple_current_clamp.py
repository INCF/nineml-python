import nineml


def get_component():

    c1 = nineml.abstraction_layer.DynamicsClass("SimpleCurrentClamp",
                                                 regimes=nineml.abstraction_layer.Regime(),
                                                 aliases=['I := i'],
                                                 analog_ports=[nineml.abstraction.SendPort('I')])

    return c1
