from .base import RandomDistributionActionVisitor
from ...componentclass.visitors.queriers import (
    ComponentClassInterfaceInferer, ComponentRequiredDefinitions,
    ComponentElementFinder, ComponentExpressionExtractor,
    ComponentDimensionResolver)


class RandomDistributionInterfaceInferer(ComponentClassInterfaceInferer,
                                         RandomDistributionActionVisitor):

    """
    Not extended from base classes currently, just mixes in the
    randomdistribution- specific action visitor to the component-class
    interface inferer.
    """
    pass


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


class RandomDistributionExpressionExtractor(ComponentExpressionExtractor,
                                            RandomDistributionActionVisitor):

    def __init__(self):
        RandomDistributionActionVisitor.__init__(
            self, require_explicit_overrides=True)
        ComponentExpressionExtractor.__init__(self)


class RandomDistributionDimensionResolver(ComponentDimensionResolver,
                                          RandomDistributionActionVisitor):
    pass
