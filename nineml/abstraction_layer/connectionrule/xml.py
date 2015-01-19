from lxml import etree
from lxml.builder import E
from nineml.exceptions import NineMLRuntimeError
from nineml.xmlns import NINEML
from ..xml import XMLReader, XMLWriter
from .base import (ComponentClass, ConnectionGenerator,
                   StandardLibraryConnectionRule)
from nineml.xmlns import nineml_namespace
from .visitors import ComponentVisitor
import nineml.abstraction_layer.connectionrule.base
from nineml.abstraction_layer.units import dimensionless


class XMLLoader(XMLLoader):

    def __init__(self, context=None):
        self.context = context

    # for now we copy and modify the XMLLoader from the "dynamics" module
    # it would be better either to have a common base class, or to have
    # a single XMLLoader that worked for all AL modules.

    def load_all_componentclasses(self, xmlroot, xml_node_filename_map):
        self.components = []
        self.component_srcs = {}
        for comp_block in xmlroot.findall(NINEML + "ComponentClass"):
            component = self.load_componentclass(comp_block)

            self.components.append(component)
            self.component_srcs[component] = xml_node_filename_map[comp_block]

    def load_componentclass(self, element):

        blocks = ('Parameter', 'ConnectionRule')
        subnodes = self.loadBlocks(element, blocks=blocks)
        # connection_rule = expect_single(subnodes["ConnectionRule"])
        connection_rule = subnodes.get("ConnectionRule", None)
        return ComponentClass(name=element.get('name'),
                              parameters=subnodes["Parameter"],
                              connection_rule=connection_rule)

    def load_connectionrule(self, element):
        if 'standardLibrary' in element.attrib:
            return StandardLibraryConnectionRule(element.get('standardLibrary'))
        else:
            for t in element.iterchildren(tag=etree.Element):
                try:
                    return ConnectionGenerator.fromXML(t)
                except NotImplementedError:
                    pass
            err = "No known implementation for ConnectionRule"
            raise NineMLRuntimeError(err)

    # These blocks map directly in to classes:
    def loadBlocks(self, element, blocks=None, check_for_spurious_blocks=True):
        """
        Creates a dictionary that maps class-types to instantiated objects
        """

        res = dict((block, []) for block in blocks)

        for t in element.iterchildren(tag=etree.Element):
            if t.tag.startswith(NINEML):
                tag = t.tag[len(NINEML):]
            else:
                tag = t.tag

            if check_for_spurious_blocks and not tag in blocks:
                    err = "Unexpected Block tag: %s " % tag
                    err += '\n Expected: %s' % ','.join(blocks)
                    raise NineMLRuntimeError(err)

            res[tag].append(XMLLoader.tag_to_loader[tag](self, t))
        return res

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "Parameter": load_parameter,
        "ConnectionRule": load_connectionrule,
    }


class XMLReader(XMLReader):
    loader = XMLLoader


class XMLWriter(ComponentVisitor):

    @classmethod
    def write(cls, component, file, flatten=True):  # @ReservedAssignment
        doc = cls.to_xml(component, flatten)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    @classmethod
    def to_xml(cls, component, flatten=True):  # @UnusedVariable
        assert isinstance(component, nineml.abstraction_layer.\
                                            connectionrule.base.ComponentClass)
        xml = XMLWriter().visit(component)
        return E.NineML(xml, xmlns=nineml_namespace)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.parameters] +
                    [component.connection_rule.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    def visit_connectionrule(self, connection_rule):
        # TODO: Only implemented built-in rules at this stage
        return E('ConnectionRule',
                 E.StandardLibrary(connection_rule.name,
                                   url=connection_rule.url))

    def visit_parameter(self, parameter):
        kwargs = {}
        if parameter.dimension != dimensionless:
            kwargs['dimension'] = parameter.dimension.name
        return E('Parameter',
                 name=parameter.name,
                 **kwargs)

