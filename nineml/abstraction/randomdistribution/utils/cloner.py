"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.utils.cloner import (
    ComponentExpandPortDefinition, ComponentExpandAliasDefinition,
    ComponentCloner)
from .visitors import RandomDistributionActionVisitor


class RandomDistributionExpandPortDefinition(RandomDistributionActionVisitor,
                                             ComponentExpandPortDefinition):

    pass


class RandomDistributionExpandAliasDefinition(RandomDistributionActionVisitor,
                                              ComponentExpandAliasDefinition):

    """
    An action-class that walks over a componentclass, and expands an alias in
    Aliases
    """

    pass


class RandomDistributionCloner(ComponentCloner):

    def visit_componentclass(self, componentclass, **kwargs):
        super(RandomDistributionCloner, self).visit_componentclass(
            componentclass)
        ccn = componentclass.__class__(
            name=componentclass.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in componentclass.parameters])
        return ccn
