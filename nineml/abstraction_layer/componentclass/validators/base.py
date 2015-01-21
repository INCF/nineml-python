"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

# from nineml.abstraction_layer.visitors import ComponentClassActionVisitor

from ..utils import ComponentClassActionVisitor


class BaseValidator(object):

    def get_warnings(self):
        raise NotImplementedError()


class PerNamespaceValidator(ComponentClassActionVisitor, BaseValidator):

    def __init__(self, require_explicit_overrides=True):
        ComponentClassActionVisitor.__init__(self,
            require_explicit_overrides=require_explicit_overrides)  # @IgnorePep8
        BaseValidator.__init__(self)

    # Override this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        namespace = component.get_node_addr()
        ComponentClassActionVisitor.visit_componentclass(self, component,
                                           namespace=namespace)
