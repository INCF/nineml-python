# encoding: utf-8
from operator import and_
from ..base import BaseULObject, Reference
from ...base import E, read_annotations, annotate_xml, NINEML
from ..utility import check_tag
from ..random import RandomDistribution
from .base import BaseComponent
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

    def __init__(self, name, value, units=None):
        if not isinstance(value, (int, float, Reference, BaseComponent)):
            raise Exception("Invalid type '{}' for value, can be one of "
                            "'Value', 'Reference', 'Component', 'ValueList', "
                            "'ExternalValueList'"
                            .format(value.__class__.__name__))
        if not isinstance(units, Unit) and units is not None:
            raise Exception("Units ({}) must of type <Unit>".format(units))
        super(Property, self).__init__()
        self.name = name
        self.value = value
        self.unit = units

    def __repr__(self):
        units = self.unit.name
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return "Property(name=%s, value=%s, unit=%s)" % (self.name,
                                                          self.value, units)

    def __eq__(self, other):
        # FIXME: obviously we should resolve the units, so 0.001 V == 1 mV,
        #        could use python-quantities package to do this if we are
        #        okay with the dependency
        return isinstance(other, self.__class__) and \
            reduce(and_, (self.name == other.name,
                          self.value == other.value,
                          self.unit == other.unit))

    def __hash__(self):
        return hash(self.name) ^ hash(self.value) ^ hash(self.unit)

    def is_random(self):
        return isinstance(self.value, RandomDistribution)

    @annotate_xml
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
    @read_annotations
    def from_xml(cls, element, context):
        check_tag(element, cls)
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
            value = BaseComponent.from_xml(value_element)
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
        return cls(name=element.attrib["name"], value, units)


class StringValue(object):

    """
    Not intended to be instantiated: just provides the from_xml() classmethod.
    """
    element_name = "Value"

    @classmethod
    @read_annotations
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
            self[name] = InitialValue(name, value, unit)

    def __repr__(self):
        return "InitialValueSet(%s)" % dict(self)

    @classmethod
    def from_xml(cls, elements, context):
        initial_values = []
        for iv_element in elements:
            initial_values.append(InitialValue.from_xml(iv_element,
                                                        context))
        return cls(*initial_values)
