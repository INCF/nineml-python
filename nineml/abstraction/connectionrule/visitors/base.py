"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.visitors import (
    ComponentVisitor, ComponentActionVisitor)
from ..base import ConnectionRule


class ConnectionRuleVisitor(ComponentVisitor):

    class_to_visit = ConnectionRule


class ConnectionRuleActionVisitor(ComponentActionVisitor,
                                  ConnectionRuleVisitor):

    def visit_componentclass(self, component_class, **kwargs):
        super(ConnectionRuleActionVisitor, self).visit_componentclass(
            component_class, **kwargs)
