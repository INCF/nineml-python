"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.annotations import annotate_xml
from nineml.xmlns import E
from nineml.annotations import read_annotations
from ...componentclass.visitors.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)


class RandomDistributionXMLLoader(ComponentClassXMLLoader):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_randomdistributionclass(self, element):
        block_names = ('Parameter',)
        blocks = self._load_blocks(element, block_names=block_names)
        return RandomDistribution(
            name=element.attrib['name'],
            parameters=blocks["Parameter"])

    tag_to_loader = dict(
        tuple(ComponentClassXMLLoader.tag_to_loader.iteritems()) +
        (("RandomDistribution", load_randomdistributionclass),))


class RandomDistributionXMLWriter(ComponentClassXMLWriter):

    # Maintains order of elements between writes
    write_order = ['Parameters', 'Alias', 'Constant', 'Annotations']

    @annotate_xml
    def visit_componentclass(self, component_class):
        return E('RandomDistribution',
                 *self._sort(e.accept_visitor(self) for e in component_class),
                 name=component_class.name)

from ..base import RandomDistribution
