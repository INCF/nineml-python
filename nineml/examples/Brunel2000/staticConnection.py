import nineml.abstraction_layer as al
from nineml.abstraction_layer.units import current

model = al.DynamicsClass(
    name="StaticConnection",
    regimes=[
        al.Regime(
            name="default",
            time_derivatives=[
                "dweight/dt = 0"],
        )
    ],
    state_variables=[
        al.StateVariable('weight', dimension=current),  # would be nice to make this dimensionless
    ],
    analog_ports=[al.AnalogSendPort("weight", dimension=current)],
)


if __name__ == "__main__":
    from nineml.abstraction_layer.dynamics.writers import XMLWriter
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    XMLWriter.write(model, filename)
