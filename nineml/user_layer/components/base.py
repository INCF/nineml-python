# encoding: utf-8
import urllib
from lxml import etree
from operator import and_
from ...abstraction_layer import BaseComponentClass
from ..base import BaseULObject, E, NINEML
from ... import abstraction_layer
import nineml.context

# This line is imported at the end of the file to avoid recursive imports
# from .interface import Property, InitialValue, InitialValueSet, PropertySet


class BaseComponent(BaseULObject):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "Component"
    defining_attributes = ("name", "definition", "properties")
    children = ("properties",)

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, name, definition=None, properties={}, reference=None,
                 initial_values={}):
        """
        Create a new component with the given name, definition and properties,
        or create a reference to another component that will be resolved later.

        `name` - a name for the component that can be used to reference it.
        `definition` - a Definition instance, the URL of a component
                       definition, or None if creating a reference.
        `properties` - a PropertySet instance or a dictionary containing
                       (value,unit) pairs.
        `reference` - the name of another component in the model, or None.
        """
        self.name = name
        if isinstance(definition, Definition):
            self.definition = definition
            assert reference is None, \
                                   "Cannot give both definition and reference."
        elif isinstance(definition, basestring):  # TODO: should also check is a valid URI @IgnorePep8
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
        if isinstance(properties, PropertySet):
            self.properties = properties
        elif isinstance(properties, dict):
            self.properties = PropertySet(**properties)
        else:
            raise TypeError("properties must be a PropertySet or a dict")
        self.reference = reference
        if isinstance(initial_values, InitialValueSet):
            self.initial_values = initial_values
        elif isinstance(initial_values, dict):
            self.initial_values = InitialValueSet(**initial_values)
        else:
            raise TypeError("initial_values must be an InitialValueSet or a "
                            "dict, not a %s" % type(initial_values))
        if not self.unresolved:
            self.check_properties()
            module_path = definition.component_class.__module__.split('.')
            if 'dynamics' in module_path:
                self.check_initial_values()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        assert not (self.unresolved or other.unresolved)
        return reduce(and_, (self.name == other.name,
                             self.definition == other.definition,
                             self.properties == other.properties))

    def __hash__(self):
        assert not self.unresolved
        return (hash(self.__class__) ^ hash(self.name) ^
                hash(self.definition) ^ hash(self.properties))

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
        if self.properties != other.properties:
            d += ["properties: %s != %s" % (self.properties, other.properties)]
        return "\n".join(d)

    @property
    def unresolved(self):
        return self.definition is None

    def resolve(self, other_component):
        """
        If the component is unresolved (contains a reference to another
        component), copy the definition and properties from the other
        component, and update those properties with the properties from this
        component.
        """
        assert other_component.__class__ == self.__class__
        assert self.reference == other_component.name
        self.definition = other_component.definition
        # note that this behaves oppositely to dict.update
        self.properties.complete(other_component.properties)
        self.check_properties()

    def get_definition(self):
        if not self.definition.component:
            self.definition.retrieve()
        return self.definition.component

    def check_properties(self):
        # First check the names
        properties = set(self.properties.iterkeys())
        parameters = set(p.name for p in self.definition.component_class.parameters)
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
        # Now check dimensions
        # TODO

    def to_xml(self):
        properties_and_initial_values = (self.properties.to_xml() +
                                         [iv.to_xml()
                                          for iv in
                                                 self.initial_values.values()])
        element = E(self.element_name,
                    self.definition.to_xml(),
                    *properties_and_initial_values,
                    name=self.name)
        return element

    @classmethod
    def from_xml(cls, element, components):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.attrib.get("name", None)
        properties = PropertySet.from_xml(
            element.findall(NINEML + Property.element_name), components)
        initial_values = InitialValueSet.from_xml(
            element.findall(NINEML + InitialValue.element_name), components)
        definition_element = element.find(NINEML + Definition.element_name)
        if definition_element is not None:
            definition = Definition.from_xml(definition_element)
            return cls(name, definition, properties,
                       initial_values=initial_values)
        else:
            reference_element = element.find(NINEML + "Reference")
            if reference_element is not None:
                return cls(name, None, properties,
                           reference=reference_element.text,
                           initial_values=initial_values)
            else:
                raise Exception("A component must contain either a defintion "
                                "or a reference")


class Definition(BaseULObject):

    """
    Encapsulate a component definition.

    For now, this holds only the URI of an abstraction layer file, but this
    could be expanded later to include definitions external to 9ML.
    """
    element_name = "Definition"
    defining_attributes = ("url",)

    def __init__(self, component_class_name, component_classes={}, url=None):
        if url:
            try:
                url_root = nineml.context.Context.from_file(url)
                component_classes = url_root.component_classes
            except:  # FIXME: Need to work out what exceptions urllib throws
                raise
        try:
            self.component_class = component_classes[component_class_name]
        except KeyError:
            raise Exception("Did not find ComponentClass matching '{}'{}"
                            .format(component_class_name,
                                   " in file '{}'".format(url) if url else ''))
        self.url = url

    def __hash__(self):
        if self._component:
            return hash(self._component)
        else:
            return hash(self.url)

    @property
    def component(self):
        return self.retrieve()

    def retrieve(self):
        reader = getattr(abstraction_layer,
                         self.abstraction_layer_module).readers.XMLReader
        if self.abstraction_layer_module == "random":  # hack
            self._component = reader.read_component(self.url)
        else:
            f = urllib.urlopen(self.url)
            try:
                component_class = reader.read_component(self.url)
            finally:
                f.close()
        return component_class

    def to_xml(self):
        if hasattr(self, "url") and self.url:
            return E(self.element_name, (E.link(self.url)), language="NineML")
        else:  # inline
            al_writer = getattr(abstraction_layer,
                                self.abstraction_layer_module).\
                                                            writers.XMLWriter()
            return E(self.element_name,
                     al_writer.visit(self._component),
                     language="NineML")

    @classmethod
    def from_xml(cls, element, component_classes=[]):
        url = element.attrib.get('url', None)
        component_class_name = element.text
        return cls(component_class_name, url=url)


class Reference(BaseULObject):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "Reference"
    defining_attributes = ("url")

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, component_name, context, url=None):
        """
        Create a new component with the given name, definition and properties,
        or create a reference to another component that will be resolved later.

        `component_name` - a name of an existing component to refer to
        `url`            - a url of the file containing the exiting component
        """
        self.url = url
        ref_context = context
        if url:
            ref_context = nineml.read(url)
        self.component = ref_context.get('Component', component_name)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return reduce(and_, (self.component_name == other.component_name,
                             self.url == other.url))

    def __hash__(self):
        assert not self.unresolved
        return (hash(self.__class__) ^ hash(self.component_name) ^
                hash(self.url))

    def __repr__(self):
            return ('{}(refers_to="{}"{})'
                    .format(self.__class__.__name__, self.component_name,
                            ' in "{}"'.format(self.url) if self.url else ''))

    def to_xml(self):
        kwargs = {'url': self.url} if self.url else {}
        element = E(self.element_name,
                    self.component_name,
                    **kwargs)
        return element

    @classmethod
    def from_xml(cls, element, context):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        component_name = element.text
        url = element.attrib.get("url", None)
        return cls(component_name, context, url)


def component_ref(xml, context):
    ref_xml = xml.find(NINEML + 'Reference')
    if ref_xml:
        return Reference.from_xml(ref_xml, context)
    else:
        return BaseComponent.from_xml(xml, context)


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

# This is imported at the end to avoid recursive imports
from .interface import Property, InitialValue, InitialValueSet, PropertySet
