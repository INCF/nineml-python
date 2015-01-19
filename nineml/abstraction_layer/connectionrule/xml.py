from lxml import etree
from lxml.builder import E
from ..base.xml import BaseXMLLoader, BaseXMLReader, BaseXMLWriter
from .base import ConnectionRuleClass
from nineml.xmlns import nineml_namespace


class XMLLoader(BaseXMLLoader):

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
        raise NotImplementedError

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
