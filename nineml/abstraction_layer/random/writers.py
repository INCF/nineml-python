from lxml import etree
from lxml.builder import E
from nineml.abstraction_layer.xmlns import nineml_namespace
from .visitors import ComponentVisitor
import nineml.abstraction_layer.random.base
from nineml.abstraction_layer.units import dimensionless


class XMLWriter(ComponentVisitor):

    @classmethod
    def write(cls, component, file, flatten=True):
        doc = cls.to_xml(component, flatten)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    @classmethod
    def to_xml(cls, component, flatten=True):
        assert isinstance(component, nineml.abstraction_layer.random.base.\
                                                                ComponentClass)
        xml = XMLWriter().visit(component)
        return E.NineML(xml, xmlns=nineml_namespace)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.parameters] +
                    [component.random_distribution.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    def visit_randomdistribution(self, random_distribution):
        # TODO: Only implemented built-in distributions at this stage
        return E('RandomDistribution',
                 E.StandardLibrary(random_distribution.name,
                                   url=random_distribution.url))

    def visit_parameter(self, parameter):
        return E('Parameter',
                 name=parameter.name,
                 dimension=parameter.dimension.name)
