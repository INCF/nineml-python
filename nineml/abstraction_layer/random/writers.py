from lxml import etree
from lxml.builder import E
from nineml.abstraction_layer.dynamics import flattening
from nineml.abstraction_layer.xmlns import nineml_namespace
from nineml.abstraction_layer.dynamics.component import ComponentClass
from ..visitors import ComponentVisitor


class XMLWriter(ComponentVisitor):

    @classmethod
    def write(cls, component, file, flatten=True):  # @ReservedAssignment
        assert isinstance(component, ComponentClass)
        if not component.is_flat():
            if not flatten:
                assert False, 'Trying to save nested models not yet supported'
            else:
                component = flattening.ComponentFlattener(component).\
                                                               reducedcomponent

        xml = XMLWriter().visit(component)
        doc = E.NineML(xml, xmlns=nineml_namespace)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.parameters] +
                    [component.random_distribution.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    def visit_randomdistribution(self, random_distribution):
        return E('RandomDistribution',
                 builtin=random_distribution.builtin_definition)
