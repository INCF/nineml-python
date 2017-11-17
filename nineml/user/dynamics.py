from itertools import chain
from nineml.user.component import Property, Component, Prototype, Definition
from nineml.exceptions import (
    NineMLUsageError, NineMLNameError, name_error, NineMLUnitMismatchError)
from nineml.base import (
    ContainerObject, DynamicPortsObject)


class Initial(Property):
    """
    Represents the initial state of a state variable
    """
    nineml_type = "Initial"

    @classmethod
    def _child_accessor_name(cls):
        return 'initial_value'


class DynamicsProperties(Component, DynamicPortsObject):
    """
    A DynamicsProperties may be regarded as a parameterized instance of a
    nineml.abstraction.Dynamics.

    Parameters
    ----------
    name : str
        a name for the component_class.
    definition : Definition
        the URL of an abstraction layer component_class class definition,
        a Definition or a Prototype instance.
    properties : List[Property]|Dict[str,Quantity]
        a dictionary containing (value,units) pairs or a
        for the component_class's properties.
    initial_values : List[Property]|Dict[str,Quantity]
        a dictionary containing (value,units) pairs or a
        for the component_class's state variables.
    """
    nineml_type = 'DynamicsProperties'
    nineml_children = Component.nineml_children + (Initial,)

    def __init__(self, name, definition, properties={}, initial_values={},
                 initial_regime=None,
                 check_initial_values=False):
        super(DynamicsProperties, self).__init__(
            name=name, definition=definition, properties=properties)
        if isinstance(initial_values, dict):
            initial_values = (Initial(name, qty)
                              for name, qty in initial_values.items())
        self.add(*initial_values)
        if check_initial_values:
            self.check_initial_values()
        self.initial_regime = initial_regime

    @property
    def component_classes(self):
        """
        Returns the component class wrapped in an iterator for duck typing
        with Selection objects
        """
        return iter([self.component_class])

    def flatten(self, name=None):
        return self.clone(name=name, clone_definitions=True)

    def get_nineml_type(self):
        return self.nineml_type

    def check_initial_values(self):
        for var in self.definition.component_class.state_variables:
            try:
                initial_value = self.initial_value(var.name)
            except KeyError:
                raise NineMLUsageError(
                    "Initial value not specified for {}".format(var.name))
            initial_units = initial_value.units
            initial_dimension = initial_units.dimension
            var_dimension = var.dimension
            if initial_dimension != var_dimension:
                raise NineMLUsageError(
                    "Dimensions for '{}' initial value, {}, in '{}' don't "
                    "match that of its definition in '{}', {}."
                    .format(var.name, initial_dimension, self.name,
                            self.component_class.name, var_dimension))

    def __getinitargs__(self):
        return (self.name, self.definition, self._properties,
                self._initial_values, self._url)

    def __getitem__(self, name):
        try:
            return self.initial_value(name).quantity
        except NineMLNameError:
            super(DynamicsProperties, self).__getitem__(name)

    def __setitem__(self, name, qty):
        try:
            self.initial_value(name).quantity = qty
        except NineMLNameError:
            super(DynamicsProperties, self).__setitem__(name, qty)

    @property
    def initial_values(self):
        if isinstance(self.definition, Prototype):
            comp = self.definition.component
            return (
                (self._initial_values[n]
                 if n in self._initial_values else comp.initial_value(n))
                for n in set(chain(self._initial_values,
                                   comp.initial_value_names)))
        else:
            return iter(self._initial_values.values())

    @name_error
    def initial_value(self, name):
        try:
            return self._initial_values[name]
        except KeyError:
            try:
                return self.definition.component.initial_value(name)
            except AttributeError:
                raise NineMLNameError(
                    "No initial value named '{}' in component class"
                    .format(name))

    @property
    def initial_regime(self):
        return self._initial_regime

    @initial_regime.setter
    def initial_regime(self, regime_name):
        if regime_name is None:
            # If regime not provided pick the regime with the most time derivs.
            # this is a bit of a hack until the state-layer is implemented
            regime_name = max(self.component_class.regimes,
                              key=lambda x: x.num_time_derivatives).name
        elif regime_name not in self.component_class.regime_names:
            raise NineMLUsageError(
                "Specified initial regime, '{}', is not a name of a regime in "
                "'{}' Dynamics class (available '{}')"
                .format(regime_name, self.component_class.name,
                        "', '".join(self.component_class.regime_names)))
        self._initial_regime = regime_name

    def set(self, prop):
        try:
            super(DynamicsProperties, self).set(prop)
        except NineMLNameError:
            try:
                state_variable = self.component_class.state_variable(prop.name)
            except NineMLNameError:
                raise NineMLNameError(
                    "'{}' Dynamics does not have a Parameter or StateVariable "
                    "named '{}'".format(self.component_class.name, prop.name))
            if prop.units.dimension != state_variable.dimension:
                raise NineMLUnitMismatchError(
                    "Dimensions for '{}' initial value ('{}') don't match that"
                    " of state variable in component class ('{}')."
                    .format(prop.name, prop.units.dimension.name,
                            state_variable.dimension.name))
            self._initial_values[prop.name] = prop

    @property
    def initial_value_names(self):
        if isinstance(self.definition, Prototype):
            return (p.name for p in self.initial_values)
        else:
            return iter(self._initial_values.keys())

    @property
    def num_initial_values(self):
        return len(list(self.initial_values))

    @property
    def attributes_with_units(self):
        return chain(
            super(DynamicsProperties, self).attributes_with_units,
            self.initial_values, *[
                v.value.distribution.properties for v in self.initial_values
                if v.value.is_random()])

    def elements(self, local=False):
        """
        Overrides the elements method in ContainerObject base class to allow
        for "local" kwarg to only iterate the members that are declared in
        this instance (i.e. not the prototype)
        """
        if local:
            return chain(iter(self._properties.values()),
                         iter(self._initial_values.values()))
        else:
            return ContainerObject.elements(self)

    def serialize_node(self, node, **options):
        super(DynamicsProperties, self).serialize_node(node, **options)
        node.children(iter(self._initial_values.values()), **options)

    @classmethod
    def unserialize_node(cls, node, **options):
        name = node.attr('name', **options)
        definition = node.child((Definition, Prototype), **options)
        properties = node.children(Property, **options)
        initial_values = node.children(Initial, **options)
        return cls(name, definition, properties=properties,
                   initial_values=initial_values)

    def serialize_node_v1(self, node, **options):
        self.serialize_node(node, **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):
        return cls.unserialize_node(node, **options)

    def analog_receive_port(self, name):
        return self.component_class.analog_receive_port(name)

    @property
    def analog_receive_ports(self):
        return self.component_class.analog_receive_ports

    @property
    def analog_receive_port_names(self):
        return self.component_class.analog_receive_port_names

    @property
    def num_analog_receive_ports(self):
        return self.component_class.num_analog_receive_ports

    def analog_send_port(self, name):
        return self.component_class.analog_send_port(name)

    @property
    def analog_send_ports(self):
        return self.component_class.analog_send_ports

    @property
    def analog_send_port_names(self):
        return self.component_class.analog_send_port_names

    @property
    def num_analog_send_ports(self):
        return self.component_class.num_analog_send_ports

    def analog_reduce_port(self, name):
        return self.component_class.analog_reduce_port(name)

    @property
    def analog_reduce_ports(self):
        return self.component_class.analog_reduce_ports

    @property
    def analog_reduce_port_names(self):
        return self.component_class.analog_reduce_port_names

    @property
    def num_analog_reduce_ports(self):
        return self.component_class.num_analog_reduce_ports

    def event_receive_port(self, name):
        return self.component_class.event_receive_port(name)

    @property
    def event_receive_ports(self):
        return self.component_class.event_receive_ports

    @property
    def event_receive_port_names(self):
        return self.component_class.event_receive_port_names

    @property
    def num_event_receive_ports(self):
        return self.component_class.num_event_receive_ports

    def event_send_port(self, name):
        return self.component_class.event_send_port(name)

    @property
    def event_send_ports(self):
        return self.component_class.event_send_ports

    @property
    def event_send_port_names(self):
        return self.component_class.event_send_port_names

    @property
    def num_event_send_ports(self):
        return self.component_class.num_event_send_ports
