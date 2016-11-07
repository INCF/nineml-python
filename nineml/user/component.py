# encoding: utf-8
from abc import ABCMeta, abstractmethod
from nineml.exceptions import (
    NineMLUnitMismatchError, NineMLRuntimeError, NineMLNameError, name_error)
from nineml.base import AnnotatedNineMLObject
from nineml.reference import (
    BaseReference, write_reference, resolve_reference)
from nineml.annotations import read_annotations, annotate_xml
from nineml.utils import ensure_valid_identifier
from nineml.xml import (
    from_child_xml, unprocessed_xml, get_xml_attr, E, extract_xmlns, NINEMLv1)
from ..abstraction import ComponentClass
from nineml.units import Quantity
from . import BaseULObject
from nineml.document import Document
from nineml.base import (
    DocumentLevelObject, ContainerObject)
from nineml.values import SingleValue, ArrayValue, RandomValue
from os import path


class Definition(BaseReference):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    nineml_type = "Definition"

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            AnnotatedNineMLObject.__init__(self)
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
                        "document due to name clash with existing {} object"
                        .format(self._referred_to.name,
                                type(self._referred_to), type(doc_obj)))
            except NineMLNameError:
                document.add(self._referred_to)
        return super(Definition, self).to_xml(document, E=E, **kwargs)

    def clone(self, memo=None, clone_definitions=False, **kwargs):
        """
        Since the document they belong to is reset for clones simply return
        the clone of the referenced object

        Parameters
        ----------
        definitions : bool
            Flat to specify whether to clone component class referenced by the
            definition or just the definition itself
        """
        if memo is None:
            memo = {}
        if clone_definitions:
            referred_to = self._referred_to.clone(
                definitions=clone_definitions, memo=memo, **kwargs)
        else:
            referred_to = self._referred_to
        return self.__class__(referred_to)


class Prototype(Definition):

    nineml_type = "Prototype"

    @property
    def component(self):
        return self._referred_to

    @property
    def component_class(self):
        return self.component.component_class


class Component(BaseULObject, DocumentLevelObject, ContainerObject):
    """
    Base class for model components.

    A Component may be regarded as a parameterized instance of a
    nineml.abstraction.ComponentClass.

    A component_class may be created either from a
    nineml.abstraction.ComponentClass  together with a set
    of properties (parameter values), or by cloning then modifying an
    existing component_class (the prototype).

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
    __metaclass__ = ABCMeta  # Abstract base class
    v1_nineml_type = 'Component'
    defining_attributes = ('_name', '_definition', '_properties')
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
        ensure_valid_identifier(name)
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        ContainerObject.__init__(self)
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
        elif (isinstance(definition, ComponentClass) or
              definition.nineml_type in ('Dynamics', 'MultiDynamics')):
            definition = Definition(definition)
        elif (isinstance(definition, Component) or
              definition.nineml_type in ('DynamicsProperties',
                                         'MultiDynamicsProperties')):
            definition = Prototype(definition)
        elif definition.nineml_type not in ('Definition', 'Prototype'):
            raise ValueError("'definition' must be either a 'Definition', "
                             "'Prototype' element or url pointing to a "
                             "dynamics class")
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
    def get_nineml_type(self):
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

    def is_base_component(self):
        return isinstance(self.definition, Prototype)

    @property
    def definition(self):
        return self._definition

    def set(self, prop):
        param = self.component_class.parameter(prop.name)
        if prop.units.dimension != param.dimension:
            raise NineMLUnitMismatchError(
                "Dimensions for '{}' property ('{}') don't match that of "
                "component_class class ('{}')."
                .format(prop.name, prop.units.dimension.name,
                        param.dimension.name))
        self._properties[prop.name] = prop

    @property
    def attributes_with_units(self):
        return self.properties

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
            msg.append("User properties of '{}' ({}) contain the following "
                       "parameters that are not present in the definition of "
                       "'{}' ({}): {}\n\n".format(
                           self.name, self.url, self.component_class.name,
                           self.component_class.url, ",".join(diff_a)))
        if diff_b:
            msg.append("Definition of '{}' ({}) contains the following "
                       "parameters that are not present in the user properties"
                       " of '{}' ({}): {}".format(
                           self.component_class.name, self.component_class.url,
                           self.name, self.url, ",".join(diff_b)))
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
        if E._namespace == NINEMLv1:
            tag = self.v1_nineml_type
        else:
            tag = self.nineml_type
        element = E(tag, self._definition.to_xml(document, E=E, **kwargs),
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
        if name in document:
            doc = document
        else:
            doc = None
        return cls(name, definition, properties=properties, document=doc)

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
                if p.value.nineml_type == 'RandomValue']

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
    def local_properties(self):
        """
        All the properties that are defined in this component rather than its
        prototype
        """
        return self._properties.itervalues()

    @property
    def local_property_names(self):
        return self._properties.itervalues()

    @property
    def num_local_properties(self):
        return len(self._properties)

    @name_error
    def local_property(self, name):
        return self._properties[name]

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

    @name_error
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
    nineml_type = "Property"
    defining_attributes = ('_name', '_quantity')

    def __init__(self, name, quantity):
        super(Property, self).__init__()
        assert isinstance(name, basestring)
        quantity = Quantity.parse(quantity)
        self._name = name
        self._quantity = quantity

    def __iter__(self):
        """For convenient tuple expansion"""
        return self.name, self.value, self.units

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
                .format(self.nineml_type, self.name, self.value, units))

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        if E._namespace == NINEMLv1:
            xml = E(self.nineml_type,
                    self.value.to_xml(document, E=E, **kwargs),
                    name=self.name,
                    units=self.units.name)
        else:
            xml = E(self.nineml_type,
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
