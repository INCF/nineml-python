"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


class ComponentVisitor(object):

    def visit(self, obj, **kwargs):
        return obj.accept_visitor(self, **kwargs)


class ComponentActionVisitor(ComponentVisitor):

    def __init__(self, require_explicit_overrides=True):
        self.require_explicit_overrides = require_explicit_overrides
        self._scopes = []

    def visit_componentclass(self, component_class, **kwargs):
        self.action_componentclass(component_class, **kwargs)
        self._scopes.append(component_class)
        for p in component_class:
            p.accept_visitor(self, **kwargs)
        popped = self._scopes.pop()
        assert popped is component_class

    def visit_parameter(self, parameter, **kwargs):
        self.action_parameter(parameter, **kwargs)

    def visit_alias(self, alias, **kwargs):
        self.action_alias(alias, **kwargs)

    def visit_constant(self, constant, **kwargs):
        self.action_constant(constant, **kwargs)

    def check_pass(self):
        if self.require_explicit_overrides:
            assert False, ("There is an overriding function missing from {}"
                           .format(self.__class__.__name__))
        else:
            pass

    # To be overridden:
    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.check_pass()
