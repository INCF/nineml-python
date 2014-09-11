# encoding: utf-8
import urllib
from operator import and_
from ...abstraction_layer import BaseComponentClass
from ..base import BaseULObject, E, NINEML
from ... import abstraction_layer
# This line is imported at the end of the file to avoid recursive imports
# from .interface import Parameter, InitialValue, InitialValueSet, ParameterSet


class Definition(BaseULObject):

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
        elif isinstance(component, BaseComponentClass): #, csa.ConnectionSetTemplate)): @IgnorePep8
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
            al_writer = getattr(abstraction_layer,
                                self.abstraction_layer_module).\
                                                            writers.XMLWriter()
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
            reader = getattr(abstraction_layer, abstraction_layer_module).\
                                                 readers.XMLLoader(element, {})
            assert len(reader.components) == 0
            return reader.components[0]


class BaseComponent(BaseULObject):

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
from .interface import Parameter, InitialValue, InitialValueSet, ParameterSet
