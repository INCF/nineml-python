"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml import etree
from nineml.xmlns import E
from . import ComponentVisitor
from ...expressions import Alias, Constant, RandomVariable, RandomDistribution
from nineml.abstraction_layer.componentclass.base import Parameter
from nineml.annotations import annotate_xml, read_annotations
from nineml.utils import expect_single
from nineml.xmlns import NINEML, MATHML
from nineml.exceptions import NineMLRuntimeError


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

    def load_connectports(self, element):
        return element.get('source'), element.get('sink')

    @read_annotations
    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_alias(self, element):
        name = element.get("name")
        rhs = self.load_single_internmaths_block(element)
        return Alias(lhs=name, rhs=rhs)

    @read_annotations
    def load_randomvariable(self, element):
        # RandomDistributions are defined in Uncertml (http://uncertml.org)
        # so have their own reader/writing functions.
        return RandomVariable(
            name=element.get('name'),
            distribution=RandomDistribution.from_xml(
                expect_single(element.getchildren()), self.document),
            units=self.document[element.get('units')])

    @read_annotations
    def load_constant(self, element):
        return Constant(name=element.get('name'),
                        value=float(element.text),
                        units=self.document[element.get('units')])

    def load_single_internmaths_block(self, element, checkOnlyBlock=True):
        if checkOnlyBlock:
            elements = list(element.iterchildren(tag=etree.Element))
            if len(elements) != 1:
                raise NineMLRuntimeError(
                    "Unexpected tags found '{}'"
                    .format("', '".join(e.tag for e in elements)))
        assert (len(element.findall(MATHML + "MathML")) +
                len(element.findall(NINEML + "MathInline"))) == 1
        if element.find(NINEML + "MathInline") is not None:
            mblock = expect_single(
                element.findall(NINEML + 'MathInline')).text.strip()
        elif element.find(MATHML + "MathML") is not None:
            mblock = self.load_mathml(
                expect_single(element.find(MATHML + "MathML")))
        return mblock

    def load_mathml(self, mathml):
        raise NotImplementedError

    def _load_blocks(self, element, block_names):
        """
        Creates a dictionary that maps class-types to instantiated objects
        """
        # Initialise loaded objects with empty lists
        loaded_objects = dict((block, []) for block in block_names)

        for t in element.iterchildren(tag=etree.Element):
            # Strip namespace
            tag = t.tag[len(NINEML):] if t.tag.startswith(NINEML) else t.tag
            if tag not in block_names:
                err = "Unexpected block tag: %s " % tag
                err += '\n Expected: %s' % ','.join(block_names)
                raise NineMLRuntimeError(err)
            loaded_objects[tag].append(self.tag_to_loader[tag](self, t))
        return loaded_objects

    tag_to_loader = {
        "Parameter": load_parameter,
        "Alias": load_alias,
        "Constant": load_constant,
        "RandomVariable": load_randomvariable
    }


class ComponentClassXMLWriter(ComponentVisitor):

    @annotate_xml
    def visit_parameter(self, parameter):
        return E(Parameter.element_name,
                 name=parameter.name,
                 dimension=parameter.dimension.name)

    @annotate_xml
    def visit_alias(self, alias):
        return E(Alias.element_name,
                 E("MathInline", alias.rhs_cstr),
                 name=alias.lhs)

    @annotate_xml
    def visit_constant(self, constant):
        return E('Constant', str(constant.value),
                 name=constant.name,
                 units=constant.units.name)

    @annotate_xml
    def visit_randomvariable(self, randomvariable):
        return E('RandomVariable',
                 randomvariable.distribution.to_xml(),
                 name=randomvariable.name,
                 units=randomvariable.units.name)


from nineml.document import Document
