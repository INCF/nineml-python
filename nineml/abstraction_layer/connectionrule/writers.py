from lxml import etree
from lxml.builder import E
from nineml.abstraction_layer.xmlns import nineml_namespace
from .visitors import ComponentVisitor
import nineml.abstraction_layer.connectionrule.base


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
        if parameter.dimension is not None:
            kwargs['dimension'] = parameter.dimension.name
        return E('Parameter',
                 name=parameter.name,
                 **kwargs)
