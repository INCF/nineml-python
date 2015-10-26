"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.annotations import annotate_xml
from nineml.xml import E, get_xml_attr
from nineml.annotations import read_annotations
from ...componentclass.visitors.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)
from .base import ConnectionRuleVisitor


class ConnectionRuleXMLLoader(ComponentClassXMLLoader, ConnectionRuleVisitor):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_connectionruleclass(self, element, **kwargs):  # @UnusedVariable
        block_names = ('Parameter',)
        blocks = self._load_blocks(element, block_names=block_names)
        return ConnectionRule(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            standard_library=get_xml_attr(element, 'standard_library',
                                          self.document, **kwargs),
            parameters=blocks["Parameter"])

    tag_to_loader = dict(
        tuple(ComponentClassXMLLoader.tag_to_loader.iteritems()) +
        (("ConnectionRule", load_connectionruleclass),))


class ConnectionRuleXMLWriter(ComponentClassXMLWriter):

    @annotate_xml
    def visit_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        return E('ConnectionRule',
                 *self._sort(e.accept_visitor(self) for e in component_class),
                 name=component_class.name,
                 standard_library=component_class.standard_library)

from ..base import ConnectionRule
