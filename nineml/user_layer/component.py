# encoding: utf-8
from itertools import chain
from lxml import etree
from ..document import BaseReference
from nineml.exceptions import NineMLUnitMismatchError
from nineml.xmlns import nineml_namespace
from ..exceptions import NineMLRuntimeError
from operator import and_
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from ..utility import expect_single, check_tag, check_units
from ..abstraction_layer.units import Unit, unitless
from .values import SingleValue, ArrayValue, ExternalArrayValue
from . import BaseULObject
from nineml.document import Document


class Reference(BaseReference):
    """
    A reference to a NineML user layer object previously defined or defined elsewhere.

    **Arguments**:
        *name*
            The name of a NineML object which already exists, or which is
            defined in a separate XML file.
        *context*
            A dictionary or :class:`Context` object containing the object
            being referred to, if the object already exists.
        *url*
            If the object is defined in a separate XML file, the URL
            of the file.

    """
    element_name = "Reference"

    def __init__(self, name, document, url=None):
        """
        docstring needed

        `name`     -- a name of an existing component to refer to
        `document` -- a Document object containing the top-level
                      objects in the current file
        `url`      -- a url of the file containing the exiting component
        """
        super(Reference, self).__init__(name, document, url)
        if not isinstance(self._referred_to, BaseULObject):
            msg = ("Reference points to a non-user-layer object '{}'"
                   .format(self._referred_to.name))
            raise NineMLRuntimeError(msg)
        self._referred_to._from_reference = self

    @property
    def user_layer_object(self):
        """The object being referred to."""
        return self._referred_to


def resolve_reference(from_xml):
    def resolving_from_xml(cls, element, document):
        if element.tag == NINEML + Reference.element_name:
            reference = Reference.from_xml(element, document)
            ul_object = reference.user_layer_object
        else:
            assert element.tag == NINEML + cls.element_name
            ul_object = from_xml(cls, element, document)
        return ul_object
    return resolving_from_xml


def write_reference(to_xml):
    def unresolving_to_xml(self, as_reference=True):
        if self._from_reference is not None and as_reference:
            xml = self._from_reference.to_xml()
        else:
            xml = to_xml(self)
        return xml
    return unresolving_to_xml


class Component(BaseULObject):
    """
    Base class for model components.

    A :class:`Component` may be regarded as a parameterized instance of a
    :class:`~nineml.abstraction_layer.ComponentClass`.

    A component may be created either from a
    :class:`~nineml.abstraction_layer.ComponentClass`  together with a set
    of properties (parameter values), or by cloning then modifying an
    existing component (the prototype).

    *Arguments*:
        `name`:
             a name for the component.
        `definition`:
             the URL of an abstraction layer component class definition,
             a :class:`Definition` or a :class:`Prototype` instance.
        `properties`:
             a dictionary containing (value,units) pairs or a
             :class:`PropertySet` for the component's properties.
        `initial_values`:
            a dictionary containing (value,units) pairs or a
            :class:`PropertySet` for the component's state variables.

    """
    element_name = "Component"
    defining_attributes = ('name', 'component_class', 'properties')
    children = ("Property", "Definition", 'Prototype')

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, name, definition, properties={}, initial_values={}):
        """
        Create a new component with the given name, definition and properties,
        or create a prototype to another component that will be resolved later.
        """
        super(Component, self).__init__()
        self.name = name
        if isinstance(definition, basestring):
            definition = Definition(name=definition.replace(".xml", ""),
                                    document=Document(_url=definition),
                                    url=definition)
        elif not (isinstance(definition, Definition) or
                  isinstance(definition, Prototype)):
            raise ValueError("'definition' must be either a 'Definition' or "
                             "'Prototype' element")
        self._definition = definition
        if isinstance(properties, PropertySet):
            self._properties = properties
        elif isinstance(properties, dict):
            self._properties = PropertySet(**properties)
        else:
            raise TypeError("properties must be a PropertySet or a dict")
        if isinstance(initial_values, InitialValueSet):
            self._initial_values = initial_values
        elif isinstance(initial_values, dict):
            self._initial_values = InitialValueSet(**initial_values)
        else:
            raise TypeError("initial_values must be an InitialValueSet or a "
                            "dict, not a %s" % type(initial_values))
        self.check_properties()
        try:
            self.check_initial_values()
        except AttributeError:  # 'check_initial_values' is only in dynamics
            pass

    @property
    def component_class(self):
        """
        Returns the component class from the definition object or the
        prototype's definition, or the prototype's prototype's definition, etc.
        depending on how the component is defined.
        """
        defn = self._definition
        while not isinstance(defn, Definition):
            defn = defn.component._definition
        return defn.component_class

    @property
    def properties(self):
        """
        The set of component properties (parameter values).
        """
        # Recursively retrieves properties defined in prototypes and updates
        # them with properties defined locally
        props = PropertySet()
        if isinstance(self._definition, Prototype):
            props.update(self._definition.component.properties)
        props.update(self._properties)
        return props

    @property
    def initial_values(self):
        """
        The set of initial values for the state variables of the component.
        """
        # Recursively retrieves initial values defined in prototypes and
        # updates them with properties defined locally
        vals = InitialValueSet()
        if isinstance(self._definition, Prototype):
            vals.update(self._definition.component.initial_values)
        vals.update(self._initial_values)
        return vals

    @property
    def units(self):
        return set(p.units for p in chain(self.properties.values(),
                                          self.initial_values.values())
                   if p.units is not None)

    def __hash__(self):
        return (hash(self.__class__) ^ hash(self.name) ^
                hash(self.component_class) ^ hash(self.properties))

    def __repr__(self):
        return ('%s(name="%s", componentclass="%s")' %
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

    def get_definition(self):
        if not self.definition.component:
            self.definition.retrieve()
        return self.definition.component

    def check_properties(self):
        # First check the names
        properties = set(self.properties.iterkeys())
        parameters = set(p.name for p in self.component_class.parameters)
        msg = []
        diff_a = properties.difference(parameters)
        diff_b = parameters.difference(properties)
        if diff_a:
            msg.append("User properties contains the following parameters "
                       "that are not present in the definition: %s" %
                       ",".join(diff_a))
        if diff_b:
            msg.append("Definition contains the following parameters that are "
                       "not present in the user properties: %s" %
                       ",".join(diff_b))
        if msg:
            # need a more specific type of Exception
            raise Exception(". ".join(msg))
        # Check dimensions match
        for param in self.component_class.parameters:
            prop_units = self.properties[param.name].units
            prop_dimension = prop_units.dimension
            param_dimension = param.dimension
            if prop_dimension != param_dimension:
                err = ("Dimensions for '{}' parameter don't match, component "
                       "class '{}', component '{}'."
                       .format(param.name, param_dimension.name,
                               prop_dimension.name))
                raise NineMLUnitMismatchError(err)

    @write_reference
    @annotate_xml
    def to_xml(self):
        """
        docstring missing, although since the decorators don't
        preserve the docstring, it doesn't matter at the moment.
        """
        properties_and_initial_values = (self._properties.to_xml() +
                                         [iv.to_xml()
                                          for iv in
                                                 self.initial_values.values()])
        element = E(self.element_name,
                    self._definition.to_xml(),
                    *properties_and_initial_values,
                    name=self.name)
        return element

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        """docstring missing"""
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.attrib.get("name", None)
        properties = PropertySet.from_xml(
            element.findall(NINEML + Property.element_name), document)
        initial_values = InitialValueSet.from_xml(
            element.findall(NINEML + InitialValue.element_name), document)
        definition_element = element.find(NINEML + Definition.element_name)
        if definition_element is not None:
            definition = Definition.from_xml(definition_element, document)
        else:
            prototype_element = element.find(NINEML + "Prototype")
            if prototype_element is None:
                raise Exception("A component must contain either a defintion "
                                "or a prototype")
            definition = Prototype.from_xml(prototype_element, document)
        return cls(name, definition, properties,
                       initial_values=initial_values)

    @property
    def used_units(self):
        return set(p.units for p in self.properties.itervalues())

    def standardize_units(self, reference_units=None,
                          reference_dimensions=None):
        """Standardized the units used to avoid naming conflicts writing to
        """
        if reference_units is None:
            reference_units = self.used_units
        if reference_dimensions is None:
            reference_dimensions = set(u.dimension for u in reference_units)
        else:
            # Ensure that the units reference the same set of dimensions
            for u in reference_units:
                if u.dimension not in reference_dimensions:
                    u.set_dimension(next(d for d in reference_units
                                         if d == u.dimension))
        for p in self.properties.itervalues():
            try:
                std_unit = next(u for u in reference_units if u == p.units)
            except StopIteration:
                continue
            p.set_units(std_unit)

    def write(self, file):  # @ReservedAssignment
        self.standardize_units()
        xml = [self.to_xml()]
        xml.extend(chain(*((u.to_xml(), u.dimension.to_xml())
                            for u in self.used_units)))
        doc = E.NineML(*xml, xmlns=nineml_namespace)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)


class Definition(BaseReference):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "Definition"

    @property
    def component_class(self):
        return self._referred_to


class Prototype(BaseReference):

    element_name = "Prototype"

    @property
    def component(self):
        return self._referred_to


class Property(BaseULObject):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = "Property"
    defining_attributes = ("name", "value", "units")

    def __init__(self, name, value, units=None):
        if not isinstance(value, (int, float, SingleValue, ArrayValue,
                                  ExternalArrayValue)):
            raise Exception("Invalid type '{}' for value, can be one of "
                            "'Value', 'Reference', 'Component', 'ValueList', "
                            "'ExternalValueList'"
                            .format(value.__class__.__name__))
        if not isinstance(units, Unit) and units is not None:
            raise Exception("Units ({}) must of type <Unit>".format(units))
        super(Property, self).__init__()
        self.name = name
        if isinstance(value, (int, float)):
            value = SingleValue(value)
        self._value = value
        self.units = units

    def __hash__(self):
        return hash(self.name) ^ hash(self.value) ^ hash(self.units)

    def is_single(self):
        return isinstance(self._value, SingleValue)

    def is_random(self):
        raise NotImplementedError

    def is_array(self):
        return (isinstance(self._value, ArrayValue) or
                isinstance(self._value, ExternalArrayValue))

    @property
    def value(self):
        if self.is_single():
            return self._value.value
        else:
            raise Exception("Cannot access single value for array or component"
                            " type")

    @property
    def quantity(self):
        """The value of the parameter (magnitude and units)."""
        return (self.value, self.units)

    @property
    def value_array(self):
        if self.is_array():
            raise NotImplementedError
        else:
            raise Exception("Cannot access value array for component or single"
                            " value types")

    @property
    def random_distribution(self):
        if self.is_random():
            return self._value.component
        else:
            raise Exception("Cannot access random distribution for component "
                            "or single value types")

    def set_units(self, units):
        self.units = units

    def __repr__(self):
        units = self.units.name
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return ("Property(name={}, value={}, units={})"
                .format(self.name, self.value, units))

    def __eq__(self, other):
        # FIXME: obviously we should resolve the units, so 0.001 V == 1 mV,
        #        could use python-quantities package to do this if we are
        #        okay with the dependency
        return isinstance(other, self.__class__) and \
            reduce(and_, (self.name == other.name,
                          self.value == other.value,
                          self.units == other.units))

    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 self._value.to_xml(),
                 name=self.name,
                 units=self.units.name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        if element.find(NINEML + 'SingleValue') is not None:
            value = SingleValue.from_xml(
                expect_single(element.findall(NINEML + 'SingleValue')),
                document)
        elif element.find(NINEML + 'ArrayValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                document)
        elif element.find(NINEML + 'ExternalArrayValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                document)
        elif element.find(NINEML + 'ComponentValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                document)
        else:
            raise Exception(
                "Did not find recognised value tag in property (found {})"
                .format(', '.join(c.tag for c in element.getchildren())))
        units_str = element.attrib.get('units', None)
        try:
            units = document[units_str] if units_str else None
        except KeyError:
            raise Exception("Did not find definition of '{}' units in the "
                            "current document.".format(units_str))
        try:
            name = element.attrib['name']
        except KeyError:
            raise Exception("Property did not have name")
        return cls(name=name, value=value,
                   units=units)


class InitialValue(Property):

    """
    temporary, longer-term plan is to use SEDML or something similar
    """
    element_name = "Initial"


class PropertySet(dict):

    """
    Container for the set of properties for a component.
    """

    def __init__(self, *properties, **kwproperties):
        """
        `*properties` - should be Property instances
        `**kwproperties` - should be name=(value,units)
        """
        dict.__init__(self)
        for prop in properties:
            self[prop.name] = prop  # should perhaps do a copy
        for name, (value, units) in kwproperties.items():
            self[name] = Property(name, value, units)

    def __hash__(self):
        return hash(tuple(self.items()))

    def __repr__(self):
        return "PropertySet(%s)" % dict(self)

    def complete(self, other_property_set):
        """
        Pull properties from another property set into this one, if they do
        not already exist in this one.
        """
        for name, parameter in other_property_set.items():
            if name not in self:
                self[name] = parameter  # again, should perhaps copy

    def get_random_distributions(self):
        return [p.value for p in self.values() if p.is_random()]

    def to_xml(self):
        # serialization is in alphabetical order
        return [self[name].to_xml() for name in sorted(self.keys())]

    @classmethod
    def from_xml(cls, elements, document):
        properties = []
        for parameter_element in elements:
            properties.append(Property.from_xml(parameter_element, document))
        return cls(*properties)


class InitialValueSet(PropertySet):

    def __init__(self, *ivs, **kwivs):
        """
        `*ivs` - should be InitialValue instances
        `**kwivs` - should be name=(value,units)
        """
        dict.__init__(self)
        for iv in ivs:
            self[iv.name] = iv  # should perhaps do a copy
        for name, (value, units) in kwivs.items():
            self[name] = InitialValue(name, value, units)

    def __repr__(self):
        return "InitialValueSet(%s)" % dict(self)

    @classmethod
    def from_xml(cls, elements, document):
        initial_values = []
        for iv_element in elements:
            initial_values.append(InitialValue.from_xml(iv_element,
                                                        document))
        return cls(*initial_values)


class DynamicsComponent(Component):

    def check_initial_values(self):
        for var in self.definition.component.state_variables:
            try:
                initial_value = self.initial_values[var.name]
            except KeyError:
                raise Exception("Initial value not specified for %s" %
                                var.name)
            check_units(initial_value.units, var.dimension)


class ConnectionRuleComponent(Component):
    """
    docstring needed
    """
    pass


class DistributionComponent(Component):
    """
    Component representing a random number distribution, e.g. normal, gamma,
    binomial.

    *Example*::

        example goes here
    """
    pass
