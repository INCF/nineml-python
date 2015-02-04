"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.annotations import annotate_xml
from nineml.utils import expect_single
from nineml.xmlns import E
from ..base import DistributionClass, DistributionBlock
from nineml.annotations import read_annotations
from ...componentclass.utils.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)


class DistributionClassXMLLoader(ComponentClassXMLLoader):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_componentclass(self, element):
        subblocks = ('Parameter', 'RandomDistribution')
        children = self._load_blocks(element, blocks=subblocks)
        distributionblock = expect_single(children["RandomDistribution"])
        return DistributionClass(name=element.get('name'),
                                 parameters=children["Parameter"],
                                 distributionblock=distributionblock)

    @read_annotations
    def load_distributionblock(self, element):
        subblocks = ()
        children = self._load_blocks(element, blocks=subblocks)  # @UnusedVariable @IgnorePep8
        return DistributionBlock(
            standard_library=element.attrib['standardLibrary'])

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "RandomDistribution": load_distributionblock
    }


class DistributionClassXMLWriter(ComponentClassXMLWriter):

    @annotate_xml
    def visit_componentclass(self, componentclass):
        elements = ([p.accept_visitor(self)
                     for p in componentclass.parameters] +
                    [componentclass._main_block.accept_visitor(self)])
        return E('ComponentClass', *elements, name=componentclass.name)

    @annotate_xml
    def visit_distributionblock(self, distributionblock):
        return E('RandomDistribution',
                 standardLibrary=distributionblock.standard_library)
