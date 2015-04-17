"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .cloner import ConnectionRuleExpandPortDefinition
from ...componentclass.utils.modifiers import (
    ComponentModifier, ComponentRenameSymbol, ComponentAssignIndices)
from .visitors import ConnectionRuleActionVisitor


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
