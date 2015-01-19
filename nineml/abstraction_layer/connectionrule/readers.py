from lxml import etree

from nineml.exceptions import NineMLRuntimeError
from nineml.xmlns import NINEML
from nineml.abstraction_layer.components import Parameter
from nineml.abstraction_layer.dynamics.readers import XMLReader
from .base import (ComponentClass, ConnectionGenerator,
                   StandardLibraryConnectionRule)
from ...utility import expect_none_or_single


class XMLLoader(object):

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

    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=element.get('dimension'))

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
