from lxml.builder import E
from nineml.utils import expect_single
from nineml.abstraction_layer.componentclass.base import Parameter
from nineml.abstraction_layer.ports import PropertySendPort
from ..base import DistributionClass, Distribution
from ...componentclass.utils.xml import (
    ComponentClassXMLWriter, ComponentClassXMLLoader)


class DistributionClassXMLLoader(ComponentClassXMLLoader):

    def load_componentclass(self, element):

        blocks = ('Parameter', 'PropertySendPort', 'Distribution')

        subnodes = self._load_blocks(element, blocks=blocks)

        distribution = expect_single(subnodes["Distribution"])
        return DistributionClass(name=element.get('name'),
                                 distribution=distribution,
                                 parameters=subnodes["Parameter"])

    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=self.document[element.get('dimension')])

    def load_propertysendport(self, element):
        return PropertySendPort(name=element.get('name'),
                                dimension=self.document[
                                    element.get('dimension')])

    def load_randomvariable(self, element):
        return Distribution()

    def load_distribution(self, element):
        blocks = ('RandomVariable',)
        subnodes = self._load_blocks(element, blocks=blocks)
        return expect_single(subnodes['RandomVariable'])

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "Distribution": load_distribution,
        "Parameter": load_parameter,
        "PropertySendPort": load_propertysendport,
        "RandomVariable": load_randomvariable
    }


class DistributionClassXMLWriter(ComponentClassXMLWriter):

    @classmethod
    def to_xml(cls, component):
        assert isinstance(component, DistributionClass)
        super(DistributionClassXMLWriter, self).to_xml(component)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.parameters] +
                    [component.distribution.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    def visit_distribution(self, distribution):
        return E('Distribution', E.Distribution())
