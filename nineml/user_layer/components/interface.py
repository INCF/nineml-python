# encoding: utf-8
import collections
from numbers import Number
from operator import and_
from ..base import BaseULObject, E, NINEML
from ..utility import check_tag
from ..random import RandomDistribution
from .base import BaseComponent, Reference
from ...abstraction_layer import Unit


class Property(BaseULObject):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, unit) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = "Property"
    defining_attributes = ("name", "quantity")

    def __init__(self, name, quantity):
        if not isinstance(quantity, Quantity):
            raise TypeError("Value must be provided as a Quantity object")
        self.name = name
        self.quantity = quantity

    @property
    def value(self):
        return self.quantity.value

    @property
    def unit(self):
        return self.quantity.units

    def __repr__(self):
        units = self.unit
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return "Property(name=%s, value=%s, unit=%s)" % (self.name,
                                                          self.value, units)

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
        return E(self.element_name,
                 self.quantity.to_xml(),
                 name=self.name)

    @classmethod
    def from_xml(cls, element, context):
        check_tag(element, cls)
        quantity = Quantity.from_xml(element.find(NINEML + "Quantity"),
                                     context)
        return cls(name=element.attrib["name"], quantity=quantity)


class Quantity(object):

    """
    Represents a "quantity", a single value, random distribution or function
    with associated units
    """
    element_name = "Quantity"

    def __init__(self, value, units):
        if not isinstance(value, (int, float, Reference, BaseComponent)):
            raise Exception("Invalid type '{}' for value, can be one of "
                            "'Value', 'Reference', 'Component', 'ValueList', "
                            "'ExternalValueList'"
                            .format(value.__class__.__name__))
        if not isinstance(units, Unit) and units is not None:
            raise Exception("Units ({}) must of type <Unit>".format(units))
        self.value = value
        self.units = units

    def to_xml(self):
        if isinstance(self.value, (int, float)):
            value_element = E('SingleValue', str(self.value))
        else:
            value_element = self.value.to_xml()
        kwargs = {'units': self.units.name} if self.units else {}
        return E(self.element_name,
                 value_element,
                 **kwargs)

    @classmethod
    def from_xml(cls, element, context):
        """
        Parse an XML ElementTree structure and return a (value, units) tuple.
        The value should be a number or something that generates a numerical
        value, e.g. a RandomDistribution instance).

        `element` - should be an ElementTree Element instance.
        """
        try:
            value_element = element.getchildren()[0]
        except IndexError:
            raise Exception("Expected child elements in Quantity element")
        if value_element.tag == NINEML + 'SingleValue':
            try:
                value = float(value_element.text)
            except ValueError:
                raise ValueError("Provided value '{}' is not numeric"
                                .format(value_element.text))
        elif value_element.tag in (NINEML + 'ArrayValue',
                                   NINEML + 'ExternalArrayValue'):
            raise NotImplementedError
        elif value_element.tag in (NINEML + 'Reference', NINEML + 'Component'):
            value = context.resolve_ref(element, BaseComponent)
        else:
            raise KeyError("Unrecognised tag name '{tag}', was expecting one "
                           "of '{nm}SingleValue', '{nm}ArrayValue', "
                           "'{nm}ExternalArrayValue', '{nm}Reference' or "
                           "'{nm}Component'"
                           .format(tag=value_element.tag, nm=NINEML))
        units_str = element.attrib.get('units', None)
        try:
            units = context[units_str] if units_str else None
        except KeyError:
            raise Exception("Did not find definition of '{}' units in the "
                            "current context.".format(units_str))
        return Quantity(value, units)


class StringValue(object):

    """
    Not intended to be instantiated: just provides the from_xml() classmethod.
    """
    element_name = "Value"

    @classmethod
    def from_xml(cls, element):
        """
        Parse an XML ElementTree structure and return a string value.

        `element` - should be an ElementTree Element instance.
        """
        return element.text


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
        `**kwproperties` - should be name=(value,unit)
        """
        dict.__init__(self)
        for prop in properties:
            self[prop.name] = prop  # should perhaps do a copy
        for name, (value, unit) in kwproperties.items():
            self[name] = Property(name, Quantity(value, unit))

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
    def from_xml(cls, elements, context):
        properties = []
        for parameter_element in elements:
            properties.append(Property.from_xml(parameter_element, context))
        return cls(*properties)


class InitialValueSet(PropertySet):

    def __init__(self, *ivs, **kwivs):
        """
        `*ivs` - should be InitialValue instances
        `**kwivs` - should be name=(value,unit)
        """
        dict.__init__(self)
        for iv in ivs:
            self[iv.name] = iv  # should perhaps do a copy
        for name, (value, unit) in kwivs.items():
            self[name] = InitialValue(name, Quantity(value, unit))

    def __repr__(self):
        return "InitialValueSet(%s)" % dict(self)

    @classmethod
    def from_xml(cls, elements, context):
        initial_values = []
        for iv_element in elements:
            initial_values.append(InitialValue.from_xml(iv_element,
                                                        context))
        return cls(*initial_values)
