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


class ConnectionRuleXMLLoader(ComponentClassXMLLoader):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_connectionruleclass(self, element):
        block_names = ('Parameter',)
        blocks = self._load_blocks(element, block_names=block_names)
        return ConnectionRule(
            name=element.get('name'),
            parameters=blocks["Parameter"])

    tag_to_loader = dict(
        tuple(ComponentClassXMLLoader.tag_to_loader.iteritems()) +
        (("ConnectionRule", load_connectionruleclass),))


class ConnectionRuleXMLWriter(ComponentClassXMLWriter):

    @annotate_xml
    def visit_componentclass(self, component_class):
        return E('ConnectionRule',
                 *[e.accept_visitor(self) for e in component_class],
                 name=component_class.name)

from ..base import ConnectionRule
