from .base import DynamicsValidator
from ...componentclass.validators.base import BaseValidator
from ..utils.visitors import DynamicsActionVisitor


class PerNamespaceValidator(DynamicsActionVisitor, BaseValidator):

    def __init__(self, require_explicit_overrides=True):
        DynamicsActionVisitor.__init__(
            self, require_explicit_overrides=require_explicit_overrides)
        BaseValidator.__init__(self)

    # Override this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        namespace = component.get_node_addr()
        DynamicsActionVisitor.visit_componentclass(
            self, component, namespace=namespace)
