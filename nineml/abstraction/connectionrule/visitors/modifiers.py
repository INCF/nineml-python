"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.visitors.modifiers import (
    ComponentModifier, ComponentRenameSymbol, ComponentAssignIndices,
    ComponentExpandPortDefinition, ComponentExpandAliasDefinition)
from .base import ConnectionRuleActionVisitor


class ConnectionRuleExpandPortDefinition(ConnectionRuleActionVisitor,
                                         ComponentExpandPortDefinition):

    pass


class ConnectionRuleExpandAliasDefinition(ConnectionRuleActionVisitor,
                                          ComponentExpandAliasDefinition):

    """
    An action-class that walks over a component_class, and expands an alias in
    Aliases
    """

    pass


class ConnectionRuleModifier(ComponentModifier):

    """Utility classes for modifying components"""

    _ExpandPortDefinition = ConnectionRuleExpandPortDefinition


class ConnectionRuleRenameSymbol(ConnectionRuleActionVisitor,
                                 ComponentRenameSymbol):

    """ Can be used for:
    Aliases
    """
    pass


class ConnectionRuleAssignIndices(ComponentAssignIndices,
                                     ConnectionRuleActionVisitor):
    pass
