from ...componentclass.visitors.queriers import (
    ComponentClassInterfaceInferer, ComponentRequiredDefinitions,
    ComponentElementFinder, ComponentExpressionExtractor,
    ComponentDimensionResolver)


class RandomDistributionInterfaceInferer(ComponentClassInterfaceInferer):

    """
    Not extended from base classes currently, just mixes in the
    randomdistribution- specific action visitor to the component-class
    interface inferer.
    """
    pass


class RandomDistributionRequiredDefinitions(ComponentRequiredDefinitions):
    pass


class RandomDistributionElementFinder(ComponentElementFinder):
    pass


class RandomDistributionExpressionExtractor(ComponentExpressionExtractor):
    pass


class RandomDistributionDimensionResolver(ComponentDimensionResolver):
    pass
