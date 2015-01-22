from nineml.xmlns import E
from ...componentclass.utils import (
    ComponentClassXMLLoader, ComponentClassXMLReader, ComponentClassXMLWriter)
from ..base import ConnectionRuleClass, ConnectionRule
from nineml.utils import expect_single


class ConnectionRuleClassXMLLoader(ComponentClassXMLLoader):

    def __init__(self, document=None):
        self.document = document

    def load_componentclass(self, element):

        blocks = ('Parameter', 'ConnectionRule')
        subnodes = self._load_blocks(element, blocks=blocks)
        connection_rule = expect_single(subnodes["ConnectionRule"])
        return ConnectionRuleClass(name=element.get('name'),
                                   parameters=subnodes["Parameter"],
                                   connection_rule=connection_rule)

    def load_connectionrule(self, element):
        return ConnectionRule()

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "ConnectionRule": load_connectionrule,
    }


class ConnectionRuleClassXMLReader(ComponentClassXMLReader):
    loader = ConnectionRuleClassXMLLoader


class ConnectionRuleClassXMLWriter(ComponentClassXMLWriter):

    @classmethod
    def to_xml(cls, component, flatten=True):
        assert isinstance(component, ConnectionRuleClass)
        super(ConnectionRuleClassXMLWriter, self).to_xml(component, flatten)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.parameters] +
                    [component.connection_rule.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    def visit_connectionrule(self, connection_rule):
        raise NotImplementedError
