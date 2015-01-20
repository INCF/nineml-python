from lxml import etree
from lxml.builder import E
from nineml.xmlns import nineml_namespace
from nineml.utility import expect_single, filter_expect_single
from nineml.xmlns import NINEML
from nineml.abstraction_layer.componentclass.base import Parameter
from nineml.abstraction_layer.ports import PropertySendPort
from .base import DistributionClass, Distribution
from nineml.abstraction_layer.componentclass.utils.xml import BaseXMLWriter
from nineml.exceptions import NineMLRuntimeError


class XMLLoader(object):

    def __init__(self, document=None):
        self.document = document

    def load_subnode(self, subnode):
        namespace = subnode.get('namespace')
        component = filter_expect_single(self.components,
                                       lambda c: c.name == subnode.get('node'))
        return namespace, component

    def load_componentclass(self, element):

        blocks = ('Parameter', 'PropertySendPort', 'Distribution')

        subnodes = self.loadBlocks(element, blocks=blocks)

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
        return Distribution()  # FIXME: Should be implemented in dev2.0 changes

    def load_distribution(self, element):
        blocks = ('RandomVariable',)
        subnodes = self.loadBlocks(element, blocks=blocks)
        # TODO: Only implemented built-in distributions at this stage
        return expect_single(subnodes['RandomVariable'])

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

            if check_for_spurious_blocks and tag not in blocks:
                    err = "Unexpected Block tag: %s " % tag
                    err += '\n Expected: %s' % ','.join(blocks)
                    raise NineMLRuntimeError(err)

            res[tag].append(XMLLoader.tag_to_loader[tag](self, t))
        return res

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "Distribution": load_distribution,
        "Parameter": load_parameter,
        "PropertySendPort": load_propertysendport,
        "RandomVariable": load_randomvariable
    }


class XMLWriter(BaseXMLWriter):

    @classmethod
    def write(cls, component, file, flatten=True):  # @ReservedAssignment
        doc = cls.to_xml(component, flatten)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    @classmethod
    def to_xml(cls, component):
        assert isinstance(component, DistributionClass)
        xml = XMLWriter().visit(component)
        return E.NineML(xml, xmlns=nineml_namespace)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.parameters] +
                    [component.distribution.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    def visit_distribution(self, distribution):
        # TODO: Only implemented built-in distributions at this stage
        return E('Distribution',
                 E.Distribution())

    def visit_parameter(self, parameter):
        return E('Parameter',
                 name=parameter.name,
                 dimension=parameter.dimension.name)
