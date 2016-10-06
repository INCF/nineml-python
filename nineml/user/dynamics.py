from itertools import chain
from nineml.reference import resolve_reference
from nineml.user.component import Property, Component, Prototype, Definition
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, name_error, NineMLUnitMismatchError)
from nineml.annotations import read_annotations
from nineml.xml import (
    from_child_xml, unprocessed_xml, get_xml_attr)
from nineml.base import (
    ContainerObject, DynamicPortsObject)


class Initial(Property):

    """
    temporary, longer-term plan is to use SEDML or something similar
    """
    nineml_type = "Initial"


class DynamicsProperties(Component, DynamicPortsObject):
    """
    Container for the set of properties for a component_class.
    """
    nineml_type = 'DynamicsProperties'
    defining_attributes = ('name', 'component_class', '_properties',
                           '_initial_values')
    class_to_member = dict(
        tuple(Component.class_to_member.iteritems()) +
        (('Initial', 'initial_value'),))
    write_order = ('Property', 'Initial')

    def __init__(self, name, definition, properties={}, initial_values={},
                 document=None, check_initial_values=False):
        super(DynamicsProperties, self).__init__(
            name=name, definition=definition, properties=properties,
            document=document)
        if isinstance(initial_values, dict):
            self._initial_values = dict(
                (name, Initial(name, qty))
                for name, qty in initial_values.iteritems())
        else:
            self._initial_values = dict((iv.name, iv) for iv in initial_values)
        if check_initial_values:
            self.check_initial_values()

    @property
    def component_classes(self):
        """
        Returns the component class wrapped in an iterator for duck typing
        with Selection objects
        """
        return iter([self.component_class])

    def get_nineml_type(self):
        return self.nineml_type

    def check_initial_values(self):
        for var in self.definition.component_class.state_variables:
            try:
                initial_value = self.initial_value(var.name)
            except KeyError:
                raise NineMLRuntimeError(
                    "Initial value not specified for {}".format(var.name))
            initial_units = initial_value.units
            initial_dimension = initial_units.dimension
            var_dimension = var.dimension
            if initial_dimension != var_dimension:
                raise NineMLRuntimeError(
                    "Dimensions for '{}' initial value, {}, in '{}' don't "
                    "match that of its definition in '{}', {}."
                    .format(var.name, initial_dimension, self.name,
                            self.component_class.name, var_dimension))

    def __getinitargs__(self):
        return (self.name, self.definition, self._properties,
                self._initial_values, self._url)

    @property
    def initial_values(self):
        if isinstance(self.definition, Prototype):
            return (
                (self._initial_values[p.name]
                 if p.name in self._initial_values else p)
                for p in self.definition.component.initial_values)
        else:
            return self._initial_values.itervalues()

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
            return self._initial_values.iterkeys()

    @property
    def num_initial_values(self):
        return len(list(self.initial_values))

    @property
    def attributes_with_units(self):
        return chain(super(DynamicsProperties, self).attributes_with_units,
                     self.initial_values)

    def elements(self, local=False):
        """
        Overrides the elements method in ContainerObject base class to allow
        for "local" kwarg to only iterate the members that are declared in
        this instance (i.e. not the prototype)
        """
        if local:
            return chain(self._properties.itervalues(),
                         self._initial_values.itervalues())
        else:
            return ContainerObject.elements(self)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        """docstring missing"""
        name = get_xml_attr(element, "name", document, **kwargs)
        definition = from_child_xml(element, (Definition, Prototype), document,
                                    **kwargs)
        properties = from_child_xml(element, Property, document, multiple=True,
                                    allow_none=True, **kwargs)
        initial_values = from_child_xml(element, Initial, document,
                                        multiple=True, allow_none=True,
                                        **kwargs)
        return cls(name, definition, properties=properties,
                   initial_values=initial_values, document=document)

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
