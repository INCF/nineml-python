"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.visitors.modifiers import (
    ComponentRenameSymbol)
from .base import BaseConnectionRuleVisitor


class ConnectionRuleRenameSymbol(ComponentRenameSymbol,
                                 BaseConnectionRuleVisitor):

    def action_connectionrule(self, connectionrule, **kwargs):
        return self.action_componentclass(connectionrule, **kwargs)
