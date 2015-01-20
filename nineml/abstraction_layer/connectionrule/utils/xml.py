from lxml import etree
from nineml.xmlns import E, NINEML
from nineml.exceptions import NineMLRuntimeError
from ...base.utils.xml import BaseXMLLoader, BaseXMLReader, BaseXMLWriter
from .base import ConnectionRuleClass, ConnectionRule
from nineml.xmlns import nineml_namespace


class XMLLoader(object):

    def __init__(self, document=None):
        self.document = document

    def load_componentclass(self, element):

        blocks = ('Parameter', 'ConnectionRule')
        subnodes = self.loadBlocks(element, blocks=blocks)
        # connection_rule = expect_single(subnodes["ConnectionRule"])
        connection_rule = subnodes.get("ConnectionRule", None)
        return ConnectionRuleClass(name=element.get('name'),
                                   parameters=subnodes["Parameter"],
                                   connection_rule=connection_rule)

    def load_connectionrule(self, element):
        return ConnectionRule()

    def load_componentclasses(self, xmlroot, xml_node_filename_map):

        self.components = []
        self.component_srcs = {}
        for comp_block in xmlroot.find(NINEML + "ComponentClass"):
            component = self.load_componentclass(comp_block)

            self.components.append(component)
            self.component_srcs[component] = xml_node_filename_map[comp_block]

    # These blocks map directly onto classes:
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

            if check_for_spurious_blocks and tag not in blocks:
                    err = "Unexpected Block tag: %s " % tag
                    err += '\n Expected: %s' % ','.join(blocks)
                    raise NineMLRuntimeError(err)

            res[tag].append(self.tag_to_loader[tag](self, t))
        return res

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "ConnectionRule": load_connectionrule,
    }


class XMLReader(BaseXMLReader):
    loader = XMLLoader


class XMLWriter(BaseXMLWriter):

    @classmethod
    def write(cls, component, file, flatten=True):  # @ReservedAssignment
        doc = cls.to_xml(component, flatten)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    @classmethod
    def to_xml(cls, component, flatten=True):  # @UnusedVariable
        assert isinstance(component, ConnectionRuleClass)
        xml = XMLWriter().visit(component)
        return E.NineML(xml, xmlns=nineml_namespace)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.parameters] +
                    [component.connection_rule.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    def visit_connectionrule(self, connection_rule):
        raise NotImplementedError
