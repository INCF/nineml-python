import collections
import urllib
from operator import and_
from .. import abstraction_layer
from . import ULobject, E, NINEML, Number, check_tag
from .random import  RandomDistribution


class Definition(ULobject):

    """
    Encapsulate a component definition.

    For now, this holds only the URI of an abstraction layer file, but this
    could be expanded later to include definitions external to 9ML.
    """
    element_name = "definition"
    defining_attributes = ("url",)

    def __init__(self, component, abstraction_layer_module=None):
        self._component = None
        if isinstance(component, basestring):
            self.url = component
        elif isinstance(component, abstraction_layer.BaseComponentClass): #, csa.ConnectionSetTemplate)): @IgnorePep8
            self._component = component
        else:
            raise TypeError("Component must be of type string or "
                            "BaseComponentClass (found {})"
                            .format(type(component)))
        # it would be better long term to infer the abstraction layer module
        # from the xml file contents, but it is simpler for now to specify it
        # explicitly.
        self.abstraction_layer_module = abstraction_layer_module

    def __hash__(self):
        if self._component:
            return hash(self._component)
        else:
            return hash(self.url)

    @property
    def component(self):
        return self.retrieve()

    def retrieve(self):
        if not self._component:
            f = urllib.urlopen(self.url)
            reader = getattr(abstraction_layer,
                             self.abstraction_layer_module).readers.XMLReader
            try:
                self._component = reader.read_component(self.url)
            finally:
                f.close()
        return self._component

    def to_xml(self):
        if hasattr(self, "url") and self.url:
            return E(self.element_name, (E.link(self.url)), language="NineML")
        else:  # inline
            al_writer = getattr(
                            abstraction_layer,
                            self.abstraction_layer_module).writers.XMLWriter()
            return E(self.element_name,
                     al_writer.visit(self._component),
                     language="NineML")

    @classmethod
    def from_xml(cls, element, abstraction_layer_module=None):
        url_element = element.find(NINEML + "link")
        if url_element is not None:
            return cls(url_element.text, abstraction_layer_module)
        else:         # handle inline abstraction layer definitions
            # this doesn't work yet because XMLReader assumes we are reading
            # from a file, doesn't allow for reading from a string, or reading
            # a sub-tree.
            reader = getattr(
                       abstraction_layer,
                       abstraction_layer_module).readers.XMLLoader(element, {})
            assert len(reader.components) == 0
            return reader.components[0]


def check_units(units, dimension):
    # primitive unit checking, should really use Pint, Quantities or Mike
    # Hull's tools
    if not dimension:
        raise ValueError("dimension not specified")
    base_units = {
        "voltage": "V",
        "current": "A",
        "conductance": "S",
        "capacitance": "F",
        "time": "s",
        "frequency": "Hz",
        "dimensionless": "",
    }
    if len(units) == 1:
        prefix = ""
        base = units
    else:
        prefix = units[0]
        base = units[1:]
    if base != base_units[dimension]:
        raise ValueError("Units %s are invalid for dimension %s" %
                         (units, dimension))


class BaseComponent(ULobject):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "component"
    defining_attributes = ("name", "definition", "parameters")
    children = ("parameters",)

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, name, definition=None, parameters={}, reference=None,
                 initial_values={}):
        """
        Create a new component with the given name, definition and parameters,
        or create a reference to another component that will be resolved later.

        `name` - a name for the component that can be used to reference it.
        `definition` - a Definition instance, the URL of a component
                       definition, or None if creating a reference.
        `parameters` - a ParameterSet instance or a dictionary containing
                       (value,unit) pairs.
        `reference` - the name of another component in the model, or None.
        """
        self.name = name
        if isinstance(definition, Definition):
            self.definition = definition
            assert reference is None, \
                                   "Cannot give both definition and reference."
        elif isinstance(definition, basestring):  # should also check is a valid uri @IgnorePep8
            self.definition = Definition(definition,
                                         self.abstraction_layer_module)
            assert reference is None, \
                                  "Cannot give both definition and reference."
        elif definition is None:
            assert reference is not None, \
                                "Either definition or reference must be given."
            assert isinstance(reference, basestring), \
                                  "reference should be the name of a component"
            self.definition = None
        else:
            raise TypeError("definition must be a Definition, a Component or "
                            "a url")
        if isinstance(parameters, ParameterSet):
            self.parameters = parameters
        elif isinstance(parameters, dict):
            self.parameters = ParameterSet(**parameters)
        else:
            raise TypeError("parameters must be a ParameterSet or a dict")
        self.reference = reference
        if isinstance(initial_values, InitialValueSet):
            self.initial_values = initial_values
        elif isinstance(initial_values, dict):
            self.initial_values = InitialValueSet(**initial_values)
        else:
            raise TypeError("initial_values must be an InitialValueSet or a "
                            "dict, not a %s" % type(initial_values))
        if not self.unresolved:
            self.check_parameters()
            if self.abstraction_layer_module == "dynamics":
                self.check_initial_values()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        assert not (self.unresolved or other.unresolved)
        return reduce(and_, (self.name == other.name,
                             self.definition == other.definition,
                             self.parameters == other.parameters))

    def __hash__(self):
        assert not self.unresolved
        return (hash(self.__class__) ^ hash(self.name) ^
                hash(self.definition) ^ hash(self.parameters))

    def __repr__(self):
        if self.definition:
            return ('%s(name="%s", definition="%s")' %
                    (self.__class__.__name__, self.name, self.definition))
        else:
            return ('%s(name="%s", UNRESOLVED)' %
                    (self.__class__.__name__, self.name))

    def diff(self, other):
        d = []
        if self.name != other.name:
            d += ["name: %s != %s" % (self.name, other.name)]
        if self.definition != other.definition:
            d += ["definition: %s != %s" % (self.definition, other.definition)]
        if self.parameters != other.parameters:
            d += ["parameters: %s != %s" % (self.parameters, other.parameters)]
        return "\n".join(d)

    @property
    def unresolved(self):
        return self.definition is None

    def resolve(self, other_component):
        """
        If the component is unresolved (contains a reference to another
        component), copy the definition and parameters from the other
        component, and update those parameters with the parameters from this
        component.
        """
        assert other_component.__class__ == self.__class__
        assert self.reference == other_component.name
        self.definition = other_component.definition
        # note that this behaves oppositely to dict.update
        self.parameters.complete(other_component.parameters)
        self.check_parameters()

    def get_definition(self):
        if not self.definition.component:
            self.definition.retrieve()
        return self.definition.component

    def check_parameters(self):
        # First check the names
        user_parameters = set(self.parameters.iterkeys())
        definition_parameters = set(
                                 p.name
                                 for p in self.definition.component.parameters)
        msg = []
        diff_a = user_parameters.difference(definition_parameters)
        diff_b = definition_parameters.difference(user_parameters)
        if diff_a:
            msg.append("User parameters contains the following parameters "
                       "that are not present in the definition: %s" %
                       ",".join(diff_a))
        if diff_b:
            msg.append("Definition contains the following parameters that are "
                       "not present in the user parameters: %s" %
                       ",".join(diff_b))
        if msg:
            # need a more specific type of Exception
            raise Exception(". ".join(msg))
        # Now check dimensions
        # TODO

    def to_xml(self):
        parameters_and_initial_values = (self.parameters.to_xml() +
                                         [iv.to_xml()
                                          for iv in
                                                 self.initial_values.values()])
        element = E(self.element_name,
                    self.definition.to_xml(),
                    *parameters_and_initial_values,
                    name=self.name)
        return element

    @classmethod
    def from_xml(cls, element, components):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.attrib.get("name", None)
        parameters = ParameterSet.from_xml(
            element.findall(NINEML + Parameter.element_name), components)
        initial_values = InitialValueSet.from_xml(
            element.findall(NINEML + InitialValue.element_name), components)
        definition_element = element.find(NINEML + Definition.element_name)
        if definition_element is not None:
            definition = Definition.from_xml(definition_element,
                                             cls.abstraction_layer_module)
            return cls(name, definition, parameters,
                       initial_values=initial_values)
        else:
            reference_element = element.find(NINEML + "reference")
            if reference_element is not None:
                return cls(name, None, parameters,
                           reference=reference_element.text,
                           initial_values=initial_values)
            else:
                raise Exception("A component must contain either a defintion "
                                "or a reference")


class Parameter(ULobject):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, unit) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = "property"
    defining_attributes = ("name", "value", "unit")

    def __init__(self, name, value, unit=None):
        self.name = name
        if (not isinstance(value, (Number, list, RandomDistribution, str)) or
            isinstance(value, bool)):
            raise TypeError("Parameter values may not be of type %s" %
                            type(value))
        self.value = value
        self.unit = unit

    def __repr__(self):
        units = self.unit
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return "Parameter(name=%s, value=%s, unit=%s)" % (self.name,
                                                          self.value, units)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            reduce(and_, (self.name == other.name,
                          self.value == other.value,
                          self.unit == other.unit))  # obviously we should resolve the units, so 0.001 V == 1 mV @IgnorePep8

    def __hash__(self):
        return hash(self.name) ^ hash(self.value) ^ hash(self.unit)

    def is_random(self):
        return isinstance(self.value, RandomDistribution)

    def to_xml(self):
        if isinstance(self.value, RandomDistribution):
            value_element = E.reference(self.value.name)
        elif (isinstance(self.value, collections.Iterable) and
              isinstance(self.value[0], Number)):
            value_element = E.array(" ".join(repr(x) for x in self.value))
        else:  # need to handle Function
            value_element = E.scalar(repr(self.value))
        return E(Parameter.element_name,
                 E.quantity(
                 E.value(   # this extra level of tags is pointless, no?
                 value_element,
                 E.unit(self.unit or "dimensionless"))),
                 name=self.name)

    @classmethod
    def from_xml(cls, element, components):
        check_tag(element, cls)
        quantity_element = element.find(NINEML +
                                        "quantity").find(NINEML + "value")
        value, unit = Value.from_xml(quantity_element, components)
        return Parameter(name=element.attrib["name"],
                         value=value,
                         unit=unit)


class Value(object):

    """
    Not intended to be instantiated: just provides the from_xml() classmethod.
    """
    element_name = "value"

    @classmethod
    def from_xml(cls, element, components):
        """
        Parse an XML ElementTree structure and return a (value, units) tuple.
        The value should be a number or something that generates a numerical
        value, e.g. a RandomDistribution instance).

        `element` - should be an ElementTree Element instance.
        """
        for name in ("reference", "scalar", "array", "function"):
            value_element = element.find(NINEML + name)
            if value_element is not None:
                break
        if value_element is None:
            raise ValueError("No value found")
        else:
            if name == "reference":
                value = get_or_create_component(value_element.text,
                                                RandomDistribution, components)
            elif name == "scalar":
                try:
                    value = float(value_element.text)
                except ValueError:
                    value = value_element.text
            elif name == "array":
                value = [float(x) for x in value_element.text.split(" ")]
            elif name == "function":
                raise NotImplementedError
        unit = element.find(NINEML + "unit").text
        return value, unit


class StringValue(object):

    """
    Not intended to be instantiated: just provides the from_xml() classmethod.
    """
    element_name = "value"

    @classmethod
    def from_xml(cls, element):
        """
        Parse an XML ElementTree structure and return a string value.

        `element` - should be an ElementTree Element instance.
        """
        return element.text


class InitialValue(ULobject):

    """
    temporary, longer-term plan is to use SEDML or something similar
    """
    element_name = "initial"
    defining_attributes = ("name", "value", "unit")

    def __init__(self, name, value, unit=None):
        self.name = name
        if (not isinstance(value, (Number, list, RandomDistribution)) or
            isinstance(value, bool)):
            raise TypeError("Initial values may not be of type %s" %
                            type(value))
        self.value = value
        self.unit = unit

    def __repr__(self):
        units = self.unit
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return ("InitialValue(name=%s, value=%s, unit=%s)" %
                (self.name, self.value, units))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            reduce(and_, (self.name == other.name,
                          self.value == other.value,
                          self.unit == other.unit))  # FIXME: obviously we should resolve the units, so 0.001 V == 1 mV @IgnorePep8

    def __hash__(self):
        return hash(self.name) ^ hash(self.value) ^ hash(self.unit)

    def is_random(self):
        return isinstance(self.value, RandomDistribution)

    def to_xml(self):
        if isinstance(self.value, RandomDistribution):
            value_element = E.reference(self.value.name)
        elif (isinstance(self.value, collections.Iterable) and
              isinstance(self.value[0], Number)):
            value_element = E.array(" ".join(repr(x) for x in self.value))
        else:  # need to handle Function
            value_element = E.scalar(repr(self.value))
        return E(InitialValue.element_name,
                 E.quantity(
                 E.value(   # this extra level of tags is pointless, no?
                 value_element,
                 E.unit(self.unit or "dimensionless"))),
                 name=self.name)

    @classmethod
    def from_xml(cls, element, components):
        check_tag(element, cls)
        quantity_element = element.find(NINEML +
                                        "quantity").find(NINEML + "value")
        value, unit = Value.from_xml(quantity_element, components)
        return InitialValue(name=element.attrib["name"],
                            value=value,
                            unit=unit)


class ParameterSet(dict):

    """
    Container for the set of parameters for a component.
    """

    def __init__(self, *parameters, **kwparameters):
        """
        `*parameters` - should be Parameter instances
        `**kwparameters` - should be name=(value,unit)
        """
        dict.__init__(self)
        for parameter in parameters:
            self[parameter.name] = parameter  # should perhaps do a copy
        for name, (value, unit) in kwparameters.items():
            self[name] = Parameter(name, value, unit)

    def __hash__(self):
        return hash(tuple(self.items()))

    def __repr__(self):
        return "ParameterSet(%s)" % dict(self)

    def complete(self, other_parameter_set):
        """
        Pull parameters from another parameter set into this one, if they do
        not already exist in this one.
        """
        for name, parameter in other_parameter_set.items():
            if name not in self:
                self[name] = parameter  # again, should perhaps copy

    def get_random_distributions(self):
        return [p.value for p in self.values() if p.is_random()]

    def to_xml(self):
        # serialization is in alphabetical order
        return [self[name].to_xml() for name in sorted(self.keys())]

    @classmethod
    def from_xml(cls, elements, components):
        parameters = []
        for parameter_element in elements:
            parameters.append(Parameter.from_xml(parameter_element,
                                                 components))
        return cls(*parameters)


class InitialValueSet(ParameterSet):

    def __init__(self, *ivs, **kwivs):
        """
        `*ivs` - should be InitialValue instances
        `**kwivs` - should be name=(value,unit)
        """
        dict.__init__(self)
        for iv in ivs:
            self[iv.name] = iv  # should perhaps do a copy
        for name, (value, unit) in kwivs.items():
            self[name] = InitialValue(name, value, unit)

    def __repr__(self):
        return "InitialValueSet(%s)" % dict(self)

    @classmethod
    def from_xml(cls, elements, components):
        initial_values = []
        for iv_element in elements:
            initial_values.append(InitialValue.from_xml(iv_element,
                                                        components))
        return cls(*initial_values)


def get_or_create_component(ref, cls, components):
    """
    Each entry in `components` is either an instance of a BaseComponent
    subclass, or the XML (elementtree Element) defining such an instance.

    If given component does not exist, we create it and replace the XML in
    `components` with the actual component. We then return the component.
    """
    assert ref in components, "%s not in %s" % (ref, components.keys())
    if not isinstance(components[ref], BaseComponent):
        components[ref] = cls.from_xml(components[ref], components)
    return components[ref]
