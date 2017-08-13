from ...componentclass.visitors.queriers import (
    ComponentRequiredDefinitions, ComponentClassInterfaceInferer,
    ComponentElementFinder, ComponentExpressionExtractor,
    ComponentDimensionResolver)


class ConnectionRuleInterfaceInferer(ComponentClassInterfaceInferer):

    """
    Not extended from base classes currently, just mixes in the connectionrule-
    specific action visitor to the component-class interface inferer.
    """
    pass


class ConnectionRuleRequiredDefinitions(ComponentRequiredDefinitions):
    pass


class ConnectionRuleElementFinder(ComponentElementFinder):
    pass


class ConnectionRuleExpressionExtractor(ComponentExpressionExtractor):
    pass


class ConnectionRuleDimensionResolver(ComponentDimensionResolver):
    pass
