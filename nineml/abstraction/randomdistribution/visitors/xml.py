"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.annotations import annotate_xml
from nineml.utils import expect_single
from nineml.xml import (
    E, get_xml_attr, unprocessed_xml, NINEMLv1, extract_xmlns)
from nineml.annotations import read_annotations
from ...componentclass.visitors.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)
from .base import RandomDistributionVisitor


class RandomDistributionXMLLoader(ComponentClassXMLLoader,
                                  RandomDistributionVisitor):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    @unprocessed_xml
    def load_randomdistributionclass(self, element, **kwargs):
        xmlns = extract_xmlns(element.tag)
        if xmlns == NINEMLv1:
            lib_elem = expect_single(element.findall(NINEMLv1 +
                                                     'RandomDistribution'))
        else:
            lib_elem = element
        blocks = self._load_blocks(
            element, block_names=('Parameter',),
            ignore=[(NINEMLv1, 'RandomDistribution')], **kwargs)
        return RandomDistribution(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            standard_library=get_xml_attr(lib_elem, 'standard_library',
                                          self.document, **kwargs),
            parameters=blocks["Parameter"])

    tag_to_loader = dict(
        tuple(ComponentClassXMLLoader.tag_to_loader.iteritems()) +
        (("RandomDistribution", load_randomdistributionclass),))


class RandomDistributionXMLWriter(ComponentClassXMLWriter,
                                  RandomDistributionVisitor):

    # Maintains order of elements between writes
    write_order = ['Parameters', 'Alias', 'Constant', 'Annotations']

    @annotate_xml
    def visit_componentclass(self, component_class):
        if self.xmlns == NINEMLv1:
            xml = self.E(
                'ComponentClass',
                self.E('ConnectionRule',
                         standardLibrary=component_class.standard_library),
                name=component_class.name)
        else:
            xml = self.E('RandomDistribution',
                         *self._sort(e.accept_visitor(self)
                                     for e in component_class),
                         name=component_class.name)
        return xml

from ..base import RandomDistribution
