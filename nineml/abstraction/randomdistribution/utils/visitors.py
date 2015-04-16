"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import (
    ComponentActionVisitor, ComponentElementFinder)
from ...componentclass.utils.visitors import ComponentRequiredDefinitions


class RandomDistributionActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, component_class, **kwargs):
        super(RandomDistributionActionVisitor, self).visit_componentclass(
            component_class, **kwargs)
        for e in component_class:
            e.accept_visitor(self, **kwargs)


class RandomDistributionRequiredDefinitions(ComponentRequiredDefinitions,
                                            RandomDistributionActionVisitor):

    def __init__(self, component_class, expressions):
        RandomDistributionActionVisitor.__init__(
            self, require_explicit_overrides=False)
        ComponentRequiredDefinitions.__init__(self, component_class,
                                              expressions)


class RandomDistributionElementFinder(ComponentElementFinder,
                                      RandomDistributionActionVisitor):

    def __init__(self, element):
        RandomDistributionActionVisitor.__init__(
            self, require_explicit_overrides=True)
        ComponentElementFinder.__init__(self, element)
