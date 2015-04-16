"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.annotations import annotate_xml
from nineml.xmlns import E
from nineml.annotations import read_annotations
from ...componentclass.utils.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)
from nineml.exceptions import handle_xml_exceptions


class RandomDistributionXMLLoader(ComponentClassXMLLoader):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    @handle_xml_exceptions
    def load_randomdistributionclass(self, element):
        block_names = ('Parameter',)
        blocks = self._load_blocks(element, block_names=block_names)
        return RandomDistributionClass(
            name=element.attrib['name'],
            parameters=blocks["Parameter"],
            url=self.document.url)

    tag_to_loader = dict(
        tuple(ComponentClassXMLLoader.tag_to_loader.iteritems()) +
        (("RandomDistributionClass", load_randomdistributionclass),))

class RandomDistributionXMLWriter(ComponentClassXMLWriter):

    @annotate_xml
    def visit_componentclass(self, component_class):
        return E('RandomDistributionClass',
                 *[e.accept_visitor(self) for e in componentclass],
                 name=component_class.name,
                 standardLibrary=componentclass.standard_library))

from ..base import RandomDistributionClass
