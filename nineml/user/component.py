# encoding: utf-8
from itertools import chain
from abc import ABCMeta, abstractmethod
from nineml.exceptions import (
    NineMLUnitMismatchError, NineMLRuntimeError, NineMLNameError)
from nineml.base import BaseNineMLObject
from nineml.reference import (
    BaseReference, write_reference, resolve_reference)
from nineml.annotations import read_annotations, annotate_xml
from nineml.utils import check_units
from nineml.xml import (
    from_child_xml, unprocessed_xml, get_xml_attr, E, extract_xmlns, NINEMLv1)
from ..abstraction import ComponentClass
from nineml.units import Quantity
from . import BaseULObject
from nineml.document import Document
from nineml.base import DocumentLevelObject, ContainerObject
from nineml.values import SingleValue, ArrayValue, RandomValue
from os import path


class Definition(BaseReference):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "Definition"

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            BaseNineMLObject.__init__(self)
            self._referred_to = args[0]
            if kwargs:
                raise NineMLRuntimeError(
                    "Cannot provide name, document or url arguments with "
                    "explicit component class")
            self._url = None
        elif not args:
            super(Definition, self).__init__(
                name=kwargs['name'], document=kwargs['document'],
                url=kwargs['url'])
        else:
            raise NineMLRuntimeError(
                "Wrong number of arguments ({}), provided to Definition "
                "__init__, can either be one (the component class) or zero"
                .format(len(args)))

    @property
    def component_class(self):
        return self._referred_to

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        if self.url is None:
            # If definition was created in Python, add component class
            # reference to document argument before writing definition
            try:
                doc_obj = document[self._referred_to.name]
                if doc_obj != self._referred_to:
                    raise NineMLRuntimeError(
                        "Cannot create reference for '{}' {} in the provided "
                        "document due to name clash with existing {} "
                        "object"
                        .format(self._referred_to.name,
                                type(self._referred_to), type(doc_obj)))
            except NineMLNameError:
                document.add(self._referred_to)
        return super(Definition, self).to_xml(document, E=E, **kwargs)


class Prototype(Definition):

    element_name = "Prototype"

    @property
    def component(self):
        return self._referred_to

    @property
    def component_class(self):
        return self.component.component_class


class Component(BaseULObject, DocumentLevelObject, ContainerObject):
    """
    Base class for model components.

    A :class:`Component` may be regarded as a parameterized instance of a
    :class:`~nineml.abstraction.ComponentClass`.

    A component_class may be created either from a
    :class:`~nineml.abstraction.ComponentClass`  together with a set
    of properties (parameter values), or by cloning then modifying an
    existing component_class (the prototype).

    *Arguments*:
        `name`:
             a name for the component_class.
        `definition`:
             the URL of an abstraction layer component_class class definition,
             a :class:`Definition` or a :class:`Prototype` instance.
        `properties`:
             a dictionary containing (value,units) pairs or a
             :class:`PropertySet` for the component_class's properties.
        `initial_values`:
            a dictionary containing (value,units) pairs or a
            :class:`PropertySet` for the component_class's state variables.

    """
    __metaclass__ = ABCMeta  # Abstract base class
    v1_element_name = 'Component'
    defining_attributes = ('name', 'component_class', '_properties')
    children = ("Property", "Definition", 'Prototype')
    write_order = ('Property',)

    class_to_member = {'Property': 'property'}

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, name, definition, properties={}, document=None):
        """
        Create a new component_class with the given name, definition and
        properties, or create a prototype to another component_class that will
        be resolved later.
        """
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        ContainerObject.__init__(self)
        self._name = name
        if isinstance(definition, basestring):
            if "#" in definition:
                defn_url, name = definition.split("#")
            else:
                defn_url, name = definition, path.basename(
                    definition).replace(".xml", "")
            definition = Definition(
                name=name,
                document=document,
                url=defn_url)
        elif isinstance(definition, ComponentClass):
            definition = Definition(definition)
        elif isinstance(definition, Component):
            definition = Prototype(definition)
        elif not (isinstance(definition, Definition) or
                  isinstance(definition, Prototype)):
            raise ValueError("'definition' must be either a 'Definition' or "
                             "'Prototype' element")
        self._definition = definition
        if isinstance(properties, dict):
            self._properties = dict((name, Property(name, qty))
                                    for name, qty in properties.iteritems())
        else:
            self._properties = dict((p.name, p) for p in properties)
        self.check_properties()

    @property
    def name(self):
        return self._name

    @abstractmethod
    def get_element_name(self):
        "Used to stop accidental construction of this class"
        pass

    def __getinitargs__(self):
        return (self.name, self.definition, self._properties, self._url)

    def __iter__(self):
        return self.properties

    def __getitem__(self, name):
        return self.property(name).quantity

    @property
    def component_class(self):
        """
        Returns the component_class class from the definition object or the
        prototype's definition, or the prototype's prototype's definition, etc.
        depending on how the component_class is defined.
        """
        defn = self.definition
        # Dereference chains of Prototypes until we get a Definition object
        while isinstance(defn, Prototype):
            defn = defn.component.definition
        return defn.component_class

    @property
    def definition(self):
        return self._definition

    def set(self, prop):
        try:
            param = self.component_class.parameter(prop.name)
        except KeyError:
            raise NineMLRuntimeError(
                "'{}' is not a parameter of components of class '{}'"
                .format(prop.name, self.component_class.name))
        if prop.units.dimension != param.dimension:
            raise NineMLUnitMismatchError(
                "Dimensions for '{}' property ('{}') don't match that of "
                "component_class class ('{}')."
                .format(prop.name, prop.units.dimension.name,
                        param.dimension.name))
        self._properties[prop.name] = prop

    @property
    def attributes_with_units(self):
        return set(p for p in self.properties if p.units is not None)

    def __repr__(self):
        return ('%s(name="%s", component_class="%s")' %
                (self.__class__.__name__, self.name,
                 self.component_class.name))

    def diff(self, other):
        d = []
        if self.name != other.name:
            d += ["name: %s != %s" % (self.name, other.name)]
        if self.definition != other.definition:
            d += ["definition: %s != %s" % (self.definition, other.definition)]
        if self.properties != other.properties:
            d += ["properties: %s != %s" % (self.properties, other.properties)]
        return "\n".join(d)

    def check_properties(self):
        # First check the names
        properties = set(self.property_names)
        parameters = set(self.component_class.parameter_names)
        msg = []
        diff_a = properties.difference(parameters)
        diff_b = parameters.difference(properties)
        if diff_a:
            msg.append("User properties of '{}' contain the following "
                       "parameters that are not present in the definition of "
                       "'{}': {}".format(self.name, self.component_class.name,
                                         ",".join(diff_a)))
        if diff_b:
            msg.append("Definition of '{}' contains the following parameters "
                       "that are not present in the user properties of '{}': "
                       "{}".format(self.component_class.name,
                                   self.name, ",".join(diff_b)))
        if msg:
            # need a more specific type of Exception
            raise NineMLRuntimeError(". ".join(msg))
        # Check dimensions match
        for param in self.component_class.parameters:
            prop_units = self.property(param.name).units
            prop_dimension = prop_units.dimension
            param_dimension = param.dimension
            if prop_dimension != param_dimension:
                raise NineMLRuntimeError(
                    "Dimensions for '{}' property, {}, in '{}' don't match "
                    "that of its definition in '{}', {}."
                    .format(param.name, prop_dimension, self.name,
                            self.component_class.name, param_dimension))

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        """
        docstring missing, although since the decorators don't
        preserve the docstring, it doesn't matter at the moment.
        """
        element = E(self.element_name,
                    self._definition.to_xml(document, E=E, **kwargs),
                    *(p.to_xml(document, E=E, **kwargs)
                      for p in self.sorted_elements(local=True)),
                      name=self.name)
        return element

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
        return cls(name, definition, properties=properties, document=document)

    @property
    def used_units(self):
        return set(p.units for p in self.properties.itervalues())

    def write(self, fname):
        """
        Writes the top-level NineML object to file in XML.
        """
        to_write = [self]
        # Also write the component class definition to file if cannot be
        # referenced from a separate url
        if self.definition.url is None:
            to_write.append(self.component_class)
        Document(*to_write).write(fname)

    def get_random_distributions(self):
        return [p.value.distribution for p in self.properties
                if p.value.element_name == 'RandomValue']

    def port(self, name):
        return self.component_class.port(name)

    @property
    def ports(self):
        return self.component_class.ports

    @property
    def port_names(self):
        return self.component_class.port_names

    @property
    def num_ports(self):
        return self.component_class.num_ports

    def send_port(self, name):
        return self.component_class.send_port(name)

    @property
    def send_ports(self):
        return self.component_class.send_ports

    @property
    def send_port_names(self):
        return self.component_class.send_port_names

    @property
    def num_send_ports(self):
        return self.component_class.num_send_ports

    def receive_port(self, name):
        return self.component_class.receive_port(name)

    @property
    def receive_ports(self):
        return self.component_class.receive_ports

    @property
    def receive_port_names(self):
        return self.component_class.receive_port_names

    @property
    def num_receive_ports(self):
        return self.component_class.num_receive_ports

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

    def elements(self, local=False):
        """
        Overrides the elements method in ContainerObject base class to allow
        for "local" kwarg to only iterate the members that are declared in
        this instance (i.e. not the prototype)
        """
        if local:
            return self._properties.itervalues()
        else:
            return ContainerObject.elements(self)

    @property
    def properties(self):
        """
        The set of component_class properties (parameter values).
        """
        # Recursively retrieves properties defined in prototypes and updates
        # them with properties defined locally
        if isinstance(self.definition, Prototype):
            return (
                self._properties[p.name] if p.name in self._properties else p
                for p in self.definition.component.properties)
        else:
            return self._properties.itervalues()

    @property
    def property_names(self):
        if isinstance(self.definition, Prototype):
            return (p.name for p in self.properties)
        else:
            return self._properties.iterkeys()

    @property
    def num_properties(self):
        return len(list(self.properties))

    # Property is declared last so as not to overwrite the 'property' decorator
    def property(self, name):
        try:
            return self._properties[name]
        except KeyError:
            try:
                return self.definition.component.property(name)
            except AttributeError:
                raise NineMLNameError(
                    "No property named '{}' in component class".format(name))


class Property(BaseULObject):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component_class that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = "Property"
    defining_attributes = ("_name", "_quantity")

    def __init__(self, name, quantity):
        super(Property, self).__init__()
        assert isinstance(name, basestring)
        quantity = Quantity.parse_quantity(quantity)
        self._name = name
        self._quantity = quantity

    @property
    def name(self):
        return self._name

    @property
    def quantity(self):
        return self._quantity

    @property
    def value(self):
        return self.quantity.value

    @property
    def units(self):
        return self.quantity.units

    def __hash__(self):
        return hash(self.name) ^ hash(self.quantity)

    def __repr__(self):
        units = self.units.name
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return ("{}(name={}, value={}, units={})"
                .format(self.element_name, self.name, self.value, units))

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        if E._namespace == NINEMLv1:
            xml = E(self.element_name,
                    self.value.to_xml(document, E=E, **kwargs),
                    name=self.name,
                    units=self.units.name)
        else:
            xml = E(self.element_name,
                    self._quantity.to_xml(document, E=E, **kwargs),
                    name=self.name)
        return xml

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        name = get_xml_attr(element, 'name', document, **kwargs)
        if extract_xmlns(element.tag) == NINEMLv1:
            value = from_child_xml(
                element,
                (SingleValue, ArrayValue, RandomValue),
                document, **kwargs)
            units = document[
                get_xml_attr(element, 'units', document, **kwargs)]
            quantity = Quantity(value, units)
        else:
            quantity = from_child_xml(
                element, Quantity, document, **kwargs)
        return cls(name=name, quantity=quantity)

    def set_units(self, units):
        self.quantity._units = units


class Initial(Property):

    """
    temporary, longer-term plan is to use SEDML or something similar
    """
    element_name = "Initial"


class DynamicsProperties(Component):
    """
    Container for the set of properties for a component_class.
    """
    element_name = 'DynamicsProperties'
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

    def get_element_name(self):
        return self.element_name

    def check_initial_values(self):
        for var in self.definition.component_class.state_variables:
            try:
                initial_value = self.initial_value(var.name)
            except KeyError:
                raise Exception("Initial value not specified for %s" %
                                var.name)
            check_units(initial_value.units, var.dimension)

    def __getinitargs__(self):
        return (self.name, self.definition, self._properties,
                self._initial_values, self._url)

    @property
    def initial_values(self):
        return self._initial_values.itervalues()

    def initial_value(self, name):
        return self._initial_values[name]

    @property
    def initial_value_names(self):
        return self._initial_values.iterkeys()

    @property
    def num_initial_values(self):
        return len(self._initial_values)

    @property
    def attributes_with_units(self):
        return (super(DynamicsProperties, self).attributes_with_units |
                set(p for p in self.initial_values if p.units is not None))

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


class ConnectionRuleProperties(Component):
    """
    docstring needed
    """
    element_name = 'ConnectionRuleProperties'

    def get_element_name(self):
        return self.element_name

    @property
    def standard_library(self):
        return self.component_class.standard_library


class RandomDistributionProperties(Component):
    """
    Component representing a random number randomdistribution, e.g. normal,
    gamma, binomial.

    *Example*::

        example goes here
    """
    element_name = 'RandomDistributionProperties'

    @property
    def standard_library(self):
        return self.component_class.standard_library

    def get_element_name(self):
        return self.element_name
