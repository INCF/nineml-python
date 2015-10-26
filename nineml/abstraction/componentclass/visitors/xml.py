"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml import etree
from nineml.xml import E
from . import ComponentVisitor
from ...expressions import Alias, Constant
from nineml.abstraction.componentclass.base import Parameter
from nineml.annotations import annotate_xml, read_annotations
from nineml.utils import expect_single
from nineml.xml import (NINEML, MATHML, extract_xmlns, get_xml_attr,
                        identify_element)
from nineml.exceptions import NineMLXMLBlockError


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
    def load_parameter(self, element, **kwargs):  # @UnusedVariable
        return Parameter(name=get_xml_attr(element, 'name', self.document,
                                           **kwargs),
                         dimension=self.document[
                             get_xml_attr(element, 'dimension', self.document,
                                          **kwargs)])

    @read_annotations
    def load_alias(self, element, **kwargs):  # @UnusedVariable
        name = get_xml_attr(element, 'name', self.document, **kwargs)
        rhs = self.load_single_internmaths_block(element)
        return Alias(lhs=name, rhs=rhs)

    @read_annotations
    def load_constant(self, element, **kwargs):  # @UnusedVariable
        return Constant(name=get_xml_attr(element, 'name', self.document,
                                          **kwargs),
                        value=get_xml_attr(element, 'value', self.document,
                                           dtype=float, **kwargs),
                        units=self.document[
                            get_xml_attr(element, 'units', self.document,
                                         **kwargs)])

    def load_single_internmaths_block(self, element, checkOnlyBlock=True):
        nineml_xmlns = extract_xmlns(element.tag)
        if checkOnlyBlock:
            elements = list(element.iterchildren(tag=etree.Element))
            if len(elements) != 1:
                raise NineMLXMLBlockError(
                    "Unexpected tags found '{}'"
                    .format("', '".join(e.tag for e in elements)))
        assert (len(element.findall(MATHML + "MathML")) +
                len(element.findall(nineml_xmlns + "MathInline"))) == 1
        if element.find(NINEML + "MathInline") is not None:
            mblock = expect_single(
                element.findall(nineml_xmlns + 'MathInline')).text.strip()
        elif element.find(MATHML + "MathML") is not None:
            mblock = self.load_mathml(
                expect_single(element.find(MATHML + "MathML")))
        return mblock

    def load_mathml(self, mathml):
        raise NotImplementedError("MathML is not currently supported but is "
                                  "planned in future versions")

    def _load_blocks(self, element, block_names):
        """
        Creates a dictionary that maps class-types to instantiated objects
        """
        # Get the XMLNS (i.e. NineML version)
        nineml_xmlns = extract_xmlns(element.tag)
        # Initialise loaded objects with empty lists
        loaded_objects = dict((block, []) for block in block_names)
        for t in element.iterchildren(tag=etree.Element):
            # Strip namespace
            tag = (t.tag[len(nineml_xmlns):]
                   if t.tag.startswith(nineml_xmlns) else t.tag)
            if tag not in block_names:
                raise NineMLXMLBlockError(
                    "Unexpected block {} within {} in '{}', expected: {}"
                    .format(tag, identify_element(element), self.document.url,
                            ','.join(block_names)))
            loaded_objects[tag].append(self.tag_to_loader[tag](self, t))
        return loaded_objects

    tag_to_loader = {
        "Parameter": load_parameter,
        "Alias": load_alias,
        "Constant": load_constant
    }


class ComponentClassXMLWriter(ComponentVisitor):

    def __init__(self, document):
        self.document = document

    @annotate_xml
    def visit_parameter(self, parameter):
        return E(Parameter.element_name,
                 name=parameter.name,
                 dimension=parameter.dimension.name)

    @annotate_xml
    def visit_alias(self, alias):
        return E(Alias.element_name,
                 E("MathInline", alias.rhs_xml),
                 name=alias.lhs)

    @annotate_xml
    def visit_constant(self, constant):
        return E('Constant',
                 name=constant.name,
                 value=str(constant.value),
                 units=constant.units.name)

    def _sort(self, elements):
        """Sorts the element into a consistent, logical order before write"""
        return sorted(
            elements,
            key=lambda e: self.write_order.index(e.tag[len(NINEML):]))


from nineml.document import Document
