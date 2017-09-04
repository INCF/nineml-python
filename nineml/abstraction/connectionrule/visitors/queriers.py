from ...componentclass.visitors.queriers import (
    ComponentRequiredDefinitions, ComponentClassInterfaceInferer,
    ComponentExpressionExtractor, ComponentDimensionResolver)
from .base import BaseConnectionRuleVisitor


class ConnectionRuleInterfaceInferer(ComponentClassInterfaceInferer,
                                     BaseConnectionRuleVisitor):

    """
    Not extended from base classes currently, just mixes in the connectionrule-
    specific action visitor to the component-class interface inferer.
    """
    pass


class ConnectionRuleRequiredDefinitions(ComponentRequiredDefinitions,
                                        BaseConnectionRuleVisitor):
    pass


class ConnectionRuleExpressionExtractor(ComponentExpressionExtractor,
                                        BaseConnectionRuleVisitor):
    pass


class ConnectionRuleDimensionResolver(ComponentDimensionResolver,
                                      BaseConnectionRuleVisitor):
    pass
