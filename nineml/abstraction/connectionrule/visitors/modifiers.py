"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.visitors.modifiers import (
    ComponentRenameSymbol, ComponentAssignIndices)


class ConnectionRuleRenameSymbol(ComponentRenameSymbol):

    """ Can be used for:
    Aliases
    """
    pass


class ConnectionRuleAssignIndices(ComponentAssignIndices):
    pass
