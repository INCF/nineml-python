"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml import etree
from . import ComponentVisitor
from ...expressions import Alias, Constant
from nineml.abstraction.componentclass.base import Parameter
from nineml.annotations import annotate_xml, read_annotations
from nineml.xml import (
    E, strip_xmlns, extract_xmlns, get_xml_attr, identify_element,
    unprocessed_xml, ALL_NINEML, NINEMLv1)
from nineml.exceptions import NineMLXMLBlockError
from nineml.abstraction.expressions import Expression


class ComponentClassXMLLoader(object):

    """This class is used by XMLReader internally.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    def __init__(self, document=None):
        if document is None:
            document = Document()
        self.document = document

    @read_annotations
    @unprocessed_xml
    def load_parameter(self, element, **kwargs):  # @UnusedVariable
        return Parameter(name=get_xml_attr(element, 'name', self.document,
                                           **kwargs),
                         dimension=self.document[
                             get_xml_attr(element, 'dimension', self.document,
                                          **kwargs)])

    @read_annotations
    @unprocessed_xml
    def load_alias(self, element, **kwargs):  # @UnusedVariable
        name = get_xml_attr(element, 'name', self.document, **kwargs)
        rhs = self.load_expression(element, **kwargs)
        return Alias(lhs=name, rhs=rhs)

    @read_annotations
    @unprocessed_xml
    def load_constant(self, element, **kwargs):  # @UnusedVariable
        xmlns = extract_xmlns(element.tag)
        if xmlns == NINEMLv1:
            value = float(element.text)
        else:
            value = get_xml_attr(element, 'value', self.document,
                                 dtype=float, **kwargs)
        return Constant(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            value=value,
            units=self.document[
                get_xml_attr(element, 'units', self.document, **kwargs)])

    def load_expression(self, element, **kwargs):
        return get_xml_attr(element, 'MathInline', self.document,
                            in_block=True, dtype=Expression, **kwargs)

    def _load_blocks(self, element, block_names, unprocessed=None,
                     prev_block_names={}, ignore=[], **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Creates a dictionary that maps class-types to instantiated objects
        """
        # Get the XML namespace (i.e. NineML version)
        xmlns = extract_xmlns(element.tag)
        assert xmlns in ALL_NINEML
        # Initialise loaded objects with empty lists
        loaded_objects = dict((block, []) for block in block_names)
        for t in element.iterchildren(tag=etree.Element):
            # Used in unprocessed_xml decorator
            if unprocessed:
                unprocessed[0].discard(t)
            # Strip namespace
            tag = (t.tag[len(xmlns):]
                   if t.tag.startswith(xmlns) else t.tag)
            if (xmlns, tag) not in ignore:
                if tag not in block_names:
                    raise NineMLXMLBlockError(
                        "Unexpected block {} within {} in '{}', expected: {}"
                        .format(tag, identify_element(element),
                                self.document.url, ', '.join(block_names)))
                loaded_objects[tag].append(self.tag_to_loader[tag](self, t))
        return loaded_objects

    tag_to_loader = {
        "Parameter": load_parameter,
        "Alias": load_alias,
        "Constant": load_constant
    }


class ComponentClassXMLWriter(ComponentVisitor):

    def __init__(self, document, E):
        self.document = document
        self.E = E

    @annotate_xml
    def visit_parameter(self, parameter):
        return self.E(Parameter.element_name,
                      name=parameter.name,
                      dimension=parameter.dimension.name)

    @annotate_xml
    def visit_alias(self, alias):
        return self.E(Alias.element_name,
                      self.E("MathInline", alias.rhs_xml),
                      name=alias.lhs)

    @annotate_xml
    def visit_constant(self, constant):
        return self.E('Constant',
                      name=constant.name,
                      value=str(constant.value),
                      units=constant.units.name)

    def _sort(self, elements):
        """Sorts the element into a consistent, logical order before write"""
        return sorted(
            elements,
            key=lambda e: self.write_order.index(strip_xmlns(e.tag)))


from nineml.document import Document
