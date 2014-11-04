from itertools import chain
from operator import itemgetter
from .base import BaseULObject, NINEML, nineml_namespace, E
from utility import check_tag
from .components.base import BaseComponent
import nineml.user_layer.population
from .projection import Projection


# class Model(BaseULObject):
# 
#     """
#     Representation of an entire 9ML model.
#     """
#     defining_attributes = ("name", "components", "groups")
#     children = ("components", "groups")
# 
#     def __init__(self, name):
#         """
#         Create an empty model with a given name.
#         """
#         self.name = name
#         self.components = {}
#         self.groups = {}
#         self._unresolved = {}
# 
#     def add_component(self, component):
#         """
#         Add a component, defined in a 9ML abstraction layer file, to the model.
# 
#         Components include spiking nodes, synapse models, random number
#         distributions, network structure representations, connection methods.
# 
#         `component` - should be a sub-class of BaseComponent.
#         """
#         assert isinstance(component, BaseComponent), type(component)
#         if component.unresolved:
#             # try to resolve it
#             if component.reference in self.components:
#                 component.resolve(self.components[component.reference])
#             # otherwise add to the list of unresolved components
#             else:
#                 self._unresolved[component.reference] = component
#         else:
#             # see if this component can be used to resolve an unresolved one
#             if component.name in self._unresolved:
#                 other_component = self._unresolved.pop(component.name)
#                 other_component.resolve(component)
#         if (component.name in self.components and
#             self.components[component.name] != component):
#             raise Exception("A different component with the name '%s' already "
#                             "exists" % component.name)
#         self.components[component.name] = component
# 
#     def _resolve_components(self):
#         for component in self.components.values():
#             if component.unresolved:
#                 component.resolve(self.components[component.reference])
# 
#     def add_group(self, group):
#         """
#         Add a group to the model. Groups contain populations of nodes, where
#         the nodes may be either individual neurons or other groups.
# 
#         `group` - should be a Network instance.
#         """
#         assert isinstance(group, Network)
#         for component in group.get_components():
#             self.add_component(component)
#         for subgroup in group.get_subgroups():
#             self.add_group(subgroup)
#         self.groups[group.name] = group
# 
#     @classmethod
#     def from_xml(cls, element):
#         """
#         Parse an XML ElementTree structure and return a Model instance.
# 
#         `element` - should be an ElementTree Element instance.
# 
#         See:
#             http://docs.python.org/library/xml.etree.elementtree.html
#             http://codespeak.net/lxml/
#         """
#         assert element.tag == NINEML + 'NineML'
#         model = cls(element.get("name"))
#         # Note that the components dict initially contains elementtree
#         # elements, but is modified within Network.from_xml(), and at the end
#         # contains Component instances.
#         components = {}
#         groups = {}
#         for child in element.findall(NINEML + BaseComponent.element_name):
#             components[child.attrib["name"]] = BaseComponent.from_xml(child,
#                                                                       [])
#         for child in element.findall(NINEML + Group.element_name):
#             group = Group.from_xml(child, components, groups)
#             model.groups[group.name] = group
#         for name, c in components.items():
#             assert isinstance(c, BaseComponent), "%s is %s" % (name, c)
#         model.components = components
#         model._resolve_components()
#         return model
# 
#     def to_xml(self):
#         """
#         Return an ElementTree representation of this model.
#         """
#         # this should determine where references can be used to avoid
#         # duplication
#         assert len(self._unresolved) == 0, str(self._unresolved)
#         root = E("nineml", xmlns=nineml_namespace, name=self.name)
#         for component in self.components.values():
#             root.append(component.to_xml())
#         for group in self.groups.values():
#             root.append(group.to_xml())
#         return root
# 
#     def write(self, filename):
#         """
#         Export this model to a file in 9ML XML format.
#         """
#         assert isinstance(filename, basestring) or (
#             hasattr(filename, "seek") and hasattr(filename, "read"))
#         etree.ElementTree(self.to_xml()).write(filename, encoding="UTF-8",
#                                                pretty_print=True,
#                                                xml_declaration=True)
# 
#     def check(self):
#         """
#         Export the model to XML, read it back in, and check that the model is
#         unchanged.
#         """
#         import StringIO
#         f = StringIO.StringIO()
#         self.write(f)
#         f.seek(0)
#         new_model = self.__class__.from_xml(etree.parse(f).getroot())
#         f.close()
#         if self != new_model:
#             find_difference(self, new_model)


def find_difference(this, that):
    assert isinstance(that, this.__class__)
    if this != that:
        if isinstance(this, BaseULObject):
            for attr in this.defining_attributes:
                a = getattr(this, attr)
                b = getattr(that, attr)
                if a != b:
                    print this, attr, this.children
                    if attr in this.children:
                        find_difference(a, b)
                    else:
                        errmsg = ("'%s' attribute of %s instance '%s' differs:"
                                  " '%r' != '%r'" % (attr,
                                                     this.__class__.__name__,
                                                     this.name, a, b))
                        if type(a) != type(b):
                            errmsg += "(%s, %s)" % (type(a), type(b))
                        raise Exception(errmsg)
        else:
            assert sorted(this.keys()) == sorted(
                that.keys())  # need to handle case of different keys
            for key in this:
                find_difference(this[key], that[key])


class PopulationGroup(BaseULObject):

    """
    Container for multiple populations
    """
    element_name = "PopulationGroup"

    def __init__(self, name, populations):
        self.name = name
        self.populations = list(populations)

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 E.Concatenate(*[E.Item(p.name, index=i)
                                 for i, p in enumerate(self.populations)]))

    @classmethod
    def from_xml(cls, element, context):
        check_tag(element, cls)
        # The only supported op at this stage
        concatenate_op = element.find(NINEML + 'Concatenate')
        if not concatenate_op:
            raise TypeError("Did not find expected 'Concatenate' child element"
                            " in 'PopulationGroup' element")
        items = []
        for child in concatenate_op.getchildren():
            if child.tag != NINEML + 'Item':
                raise TypeError("Was expecting only 'Item' elements, found "
                                "'{}'".format(child.tag))
            items.append((child.attrib['index'], context[child.text]))
        items.sort(key=itemgetter(0))
        return cls(element.attrib['name'], (p for _, p in items))


class Network(BaseULObject):

    """
    Container for populations and projections between those populations. May be
    used as the node prototype within a population, allowing hierarchical
    structures.
    """
    element_name = "Network"
    defining_attributes = ("name", "populations", "projections", "selections")
    children = ("populations", "projections", "selections")

    def __init__(self, name):
        self.name = name
        self.populations = {}
        self.projections = {}
        self.selections = {}

    def add(self, *objs):
        """
        Add one or more Population, Projection or Selection instances to the
        network.
        """
        for obj in objs:
            if isinstance(obj, nineml.user_layer.population.Population):
                self.populations[obj.name] = obj
            elif isinstance(obj, Projection):
                self.projections[obj.name] = obj
            elif isinstance(obj, nineml.user_layer.population.Selection):
                self.selections[obj.name] = obj
            else:
                raise Exception("Groups may only contain Populations, "
                                "Projections, Selections or Groups")

    def _resolve_population_references(self):
        for prj in self.projections.values():
            for name in ('source', 'target'):
                if prj.references[name] in self.populations:
                    obj = self.populations[prj.references[name]]
                elif prj.references[name] in self.selections:
                    obj = self.selections[prj.references[name]]
                elif prj.references[name] == self.name:
                    obj = self
                else:
                    raise Exception("Unable to resolve population/selection "
                                    "reference ('%s') for %s of %s" %
                                    (prj.references[name], name, prj))
                setattr(prj, name, obj)

    def get_components(self):
        components = []
        for p in chain(self.populations.values(), self.projections.values()):
            components.extend(p.get_components())
        return components

    def get_subnetworks(self):
        return [p.prototype for p in self.populations.values()
                if isinstance(p.prototype, Network)]

    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[p.to_xml() for p in chain(self.populations.values(),
                                             self.selections.values(),
                                             self.projections.values())])

    @classmethod
    def from_xml(cls, element, context):
        check_tag(element, cls)
        network = cls(name=element.attrib["name"])
        for child in element.getchildren():
            if child.tag == NINEML + nineml.user_layer.population.Population.element_name:
                obj = nineml.user_layer.population.Population.from_xml(child,
                                                                       context)
            elif child.tag == NINEML + Projection.element_name:
                obj = Projection.from_xml(child, context)
            elif child.tag == NINEML + nineml.user_layer.population.Selection.element_name:
                obj = nineml.user_layer.population.Selection.from_xml(child,
                                                                      context)
            else:
                raise Exception("<%s> elements may not contain <%s> elements" %
                                (cls.element_name, child.tag))
            network.add(obj)
        network._resolve_population_references()
        return network
