import nineml


def get_component():

    c1 = nineml.abstraction.ComponentClass("SimpleCurrentClamp",
                                                 regimes=nineml.abstraction.Regime(),
                                                 aliases=['I := i'],
                                                 analog_ports=[nineml.abstraction.SendPort('I')])

    return c1
