from ...componentclass.visitors.queriers import (
    ComponentClassInterfaceInferer, ComponentRequiredDefinitions,
    ComponentExpressionExtractor, ComponentDimensionResolver)
from .base import BaseRandomDistributionVisitor


class RandomDistributionInterfaceInferer(ComponentClassInterfaceInferer,
                                         BaseRandomDistributionVisitor):

    """
    Not extended from base classes currently, just mixes in the
    randomdistribution- specific action visitor to the component-class
    interface inferer.
    """
    pass


class RandomDistributionRequiredDefinitions(ComponentRequiredDefinitions,
                                            BaseRandomDistributionVisitor):
    pass


class RandomDistributionExpressionExtractor(ComponentExpressionExtractor,
                                            BaseRandomDistributionVisitor):
    pass


class RandomDistributionDimensionResolver(ComponentDimensionResolver,
                                          BaseRandomDistributionVisitor):
    pass
