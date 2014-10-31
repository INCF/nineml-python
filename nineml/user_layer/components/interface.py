# encoding: utf-8
import collections
from numbers import Number
from operator import and_
from ..base import BaseULObject, E, NINEML
from ..utility import check_tag
from ..random import RandomDistribution
from .base import BaseComponent, Reference


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
        if not isinstance(Quantity, quantity):
            raise Exception("Value must be provided as a Quantity object")
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
    def from_xml(cls, element, components):
        check_tag(element, cls)
        quantity = Quantity.from_xml(element.find(NINEML + "Quantity"),
                                     components)
        return Property(name=element.attrib["name"],
                         value=quantity.value,
                         unit=quantity.unit)


class Quantity(object):

    """
    Represents a "quantity", a single value, random distribution or function
    with associated units
    """
    element_name = "Quantity"

    def __init__(self, value, units):
        if not (isinstance(value, float) or isinstance(value, Reference) or
                isinstance(value, BaseComponent)):
            raise Exception("Invalid type '{}' for value, can be one of "
                            "'Value', 'Reference', 'Component', 'ValueList', "
                            "'ExternalValueList'"
                            .format(value.__class__.__name__))
        if not isinstance(units, basestring):
            raise Exception("Units ({}) must be a string".format(units))
        self.value = value
        self.units = units

    def to_xml(self):
        if isinstance(self.value, float):
            value_element = E('Value', self.value)
        else:
            value_element = self.value.to_xml()
        kwargs = {'units': self.units} if self.units else {}
        return E(self.element_name,
                 value_element,
                 **kwargs)

    @classmethod
    def from_xml(cls, element, components):
        """
        Parse an XML ElementTree structure and return a (value, units) tuple.
        The value should be a number or something that generates a numerical
        value, e.g. a RandomDistribution instance).

        `element` - should be an ElementTree Element instance.
        """
        value_element = element.getchildren()[0]
        if value_element.tag == 'Value':
            try:
                value = float(value_element.text)
            except ValueError:
                raise Exception("Provided value '{}' is not numeric"
                                .format(value_element.text))
        elif value_element.tag == 'Reference':
            # FIXME: Need to add option to read Function component type
            value = Reference.from_xml(value_element, components)
        elif value_element.tag == 'Component':
            value = BaseComponent.from_xml(value_element, components)
        elif value_element.tag in ('ValueList', 'ExternalValueList'):
            raise NotImplementedError()
        else:
            raise Exception("Unrecognised element '{}' was expecting one of "
                            "'Value', 'Reference', 'Component', 'ValueList', "
                            "'ExternalValueList'".format(element.tag))
        units = element.attrib.get('units')
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


class InitialValue(BaseULObject):

    """
    temporary, longer-term plan is to use SEDML or something similar
    """
    element_name = "Initial"
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
                                        "Quantity").find(NINEML + "Quantity")
        value, unit = Quantity.from_xml(quantity_element, components)
        return InitialValue(name=element.attrib["name"],
                            value=value,
                            unit=unit)


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
            self[name] = Property(name, value, unit)

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
    def from_xml(cls, elements, components):
        properties = []
        for parameter_element in elements:
            properties.append(Property.from_xml(parameter_element,
                                                 components))
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
