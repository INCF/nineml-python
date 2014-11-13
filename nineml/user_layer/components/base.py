# encoding: utf-8
from ..base import BaseULObject, resolve_reference, write_reference
from ...base import E, read_annotations, annotate_xml, NINEML
from ...context import BaseReference
from nineml.exceptions import NineMLUnitMismatchError


# This line is imported at the end of the file to avoid recursive imports
# from .interface import Property, InitialValue, InitialValueSet, PropertySet


class BaseComponent(BaseULObject):

    """
    Base class for model components that are defined in the abstraction layer.
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

        `name` - a name for the component that can be used to prototype it.
        `definition` - a Definition instance, the URL of a component
                       definition, or None if creating a prototype.
        `properties` - a PropertySet instance or a dictionary containing
                       (value,unit) pairs.
        `prototype` - the name of another component in the model, or None.
        """
        super(BaseComponent, self).__init__()
        self.name = name
        if not (isinstance(definition, Definition) or
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
        Recursively retrieves properties defined in prototypes and updates them
        with properties defined locally
        """
        props = PropertySet()
        if isinstance(self._definition, Prototype):
            props.update(self._definition.component.properties)
        props.update(self._properties)
        return props

    @property
    def initial_values(self):
        """
        Recursively retrieves initial values defined in prototypes and updates
        them with properties defined locally
        """
        vals = InitialValueSet()
        if isinstance(self._definition, Prototype):
            vals.update(self._definition.component.initial_values)
        vals.update(self._initial_values)
        return vals

#     def __eq__(self, other):
#         if not isinstance(other, self.__class__):
#             return False
#         return reduce(and_, (self.name == other.name,
#                              self.component_class == other.component_class,
#                              self.properties == other.properties))

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
            prop_units = self.properties[param.name].unit
            prop_dimension = prop_units.dimension if prop_units else None
            param_dimension = param.dimension
            if prop_dimension != param_dimension:
                err = ("Dimensions for '{}' parameter don't match, component "
                       "class '{}', component '{}'."
                       .format(param.name, param_dimension.name,
                               prop_dimension.name))
                raise NineMLUnitMismatchError(err)
        # TODO: Now check dimensions

    @write_reference
    @annotate_xml
    def to_xml(self):
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
    def from_xml(cls, element, context):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.attrib.get("name", None)
        properties = PropertySet.from_xml(
                               element.findall(NINEML + Property.element_name),
                                  context)
        initial_values = InitialValueSet.from_xml(
                           element.findall(NINEML + InitialValue.element_name),
                           context)
        definition_element = element.find(NINEML + Definition.element_name)
        if definition_element is not None:
            definition = Definition.from_xml(definition_element, context)
        else:
            prototype_element = element.find(NINEML + "Prototype")
            if prototype_element is None:
                raise Exception("A component must contain either a defintion "
                                "or a prototype")
            definition = Prototype.from_xml(prototype_element, context)
        return cls(name, definition, properties,
                       initial_values=initial_values)


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


# This is imported at the end to avoid recursive imports
from .interface import Property, InitialValue, InitialValueSet, PropertySet
