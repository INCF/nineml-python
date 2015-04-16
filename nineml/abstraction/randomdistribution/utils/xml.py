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
    def load_componentclass(self, element):
        block_names = ('Parameter',)
        blocks = self._load_blocks(element, blocks=block_names)
        return RandomDistributionClass(
            name=element.attrib['name'],
            parameters=blocks["Parameter"],
            standard_library=element.attrib['standardLibrary'],
            url=self.document.url)

    tag_to_loader = {
        "ComponentClass": load_componentclass
    }


class RandomDistributionXMLWriter(ComponentClassXMLWriter):

    @annotate_xml
    def visit_componentclass(self, componentclass):
        return E('ComponentClass',
                 *[e.accept_visitor(self) for e in componentclass],
                 name=componentclass.name,
                 standardLibrary=componentclass.standard_library)

from ..base import RandomDistributionClass
