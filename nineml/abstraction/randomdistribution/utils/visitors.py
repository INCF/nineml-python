"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import (
    ComponentActionVisitor, ComponentElementFinder)
from ...componentclass.utils.visitors import ComponentRequiredDefinitions


class RandomDistributionActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        super(RandomDistributionActionVisitor, self).visit_componentclass(
            componentclass, **kwargs)
        for e in componentclass:
            e.accept_visitor(self, **kwargs)


class RandomDistributionRequiredDefinitions(ComponentRequiredDefinitions,
                                            RandomDistributionActionVisitor):

    def __init__(self, componentclass, expressions):
        RandomDistributionActionVisitor.__init__(
            self, require_explicit_overrides=False)
        ComponentRequiredDefinitions.__init__(self, componentclass,
                                              expressions)


class RandomDistributionElementFinder(ComponentElementFinder,
                                      RandomDistributionActionVisitor):

    def __init__(self, element):
        RandomDistributionActionVisitor.__init__(
            self, require_explicit_overrides=True)
        ComponentElementFinder.__init__(self, element)
