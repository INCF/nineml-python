
class BaseValidator(object):

    def get_warnings(self):
        raise NotImplementedError()

from ..visitors import ActionVisitor


class PerNamespaceValidator(ActionVisitor, BaseValidator):

    def __init__(self, explicitly_require_action_overrides=True):
        ActionVisitor.__init__(
            self, explicitly_require_action_overrides=explicitly_require_action_overrides)  # @IgnorePep8
        BaseValidator.__init__(self)

    # Over-ride this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        namespace = component.get_node_addr()
        ActionVisitor.visit_componentclass(self, component,
                                           namespace=namespace)

from .general import (
    AliasesAreNotRecursiveValidator, NoDuplicatedObjectsValidator)
from .equality_checker import ComponentEqualityChecker
