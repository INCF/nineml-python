from .base import ConnectionRuleActionVisitor
from ...componentclass.visitors.queriers import (
    ComponentRequiredDefinitions, ComponentClassInterfaceInferer,
    ComponentElementFinder)


class ConnectionRuleInterfaceInferer(ComponentClassInterfaceInferer,
                                        ConnectionRuleActionVisitor):

    """
    Not extended from base classes currently, just mixes in the connectionrule-
    specific action visitor to the component-class interface inferer.
    """
    pass


class ConnectionRuleRequiredDefinitions(ComponentRequiredDefinitions,
                                        ConnectionRuleActionVisitor):

    def __init__(self, component_class, expressions):
        ConnectionRuleActionVisitor.__init__(self,
                                             require_explicit_overrides=False)
        ComponentRequiredDefinitions.__init__(self, component_class,
                                              expressions)


class ConnectionRuleElementFinder(ComponentElementFinder,
                                  ConnectionRuleActionVisitor):

    def __init__(self, element):
        ConnectionRuleActionVisitor.__init__(self,
                                             require_explicit_overrides=True)
        ComponentElementFinder.__init__(self, element)
