# encoding: utf-8
from operator import and_
from ..base import BaseULObject
from ...base import E, read_annotations, annotate_xml, NINEML
from ..utility import check_tag
from ...utility import expect_single  #FIXME: really should only have one utility @IgnorePep8
from .base import BaseComponent
from ...abstraction_layer.units import Unit, unitless
from ..values import (SingleValue, ArrayValue, ExternalArrayValue,
                      ComponentValue)


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
                                  ExternalArrayValue, ComponentValue)):
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
        return isinstance(self._value, ComponentValue)

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
        if self.units is not None:
            units = self.units.name
            if u"µ" in units:
                units = units.replace(u"µ", "u")
        else:
            units = self.units
        return "Property(name=%s, value=%s, units=%s)" % (self.name,
                                                          self.value, units)

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
        kwargs = {'name': self.name}
        if self.units:
            kwargs['units'] = self.units.name
        return E(self.element_name,
                 self._value.to_xml(),
                 **kwargs)

    @classmethod
    @read_annotations
    def from_xml(cls, element, context):
        check_tag(element, cls)
        if element.find(NINEML + 'SingleValue') is not None:
            value = SingleValue.from_xml(
                expect_single(element.findall(NINEML + 'SingleValue')),
                context)
        elif element.find(NINEML + 'ArrayValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                context)
        elif element.find(NINEML + 'ExternalArrayValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                context)
        elif element.find(NINEML + 'ComponentValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                context)
        else:
            raise Exception(
                "Did not find recognised value tag in property (found {})"
                .format(', '.join(c.tag for c in element.getchildren())))
        units_str = element.attrib.get('units', None)
        try:
            units = context[units_str] if units_str else None
        except KeyError:
            raise Exception("Did not find definition of '{}' units in the "
                            "current context.".format(units_str))
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
    def from_xml(cls, elements, context):
        properties = []
        for parameter_element in elements:
            properties.append(Property.from_xml(parameter_element, context))
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
    def from_xml(cls, elements, context):
        initial_values = []
        for iv_element in elements:
            initial_values.append(InitialValue.from_xml(iv_element,
                                                        context))
        return cls(*initial_values)
