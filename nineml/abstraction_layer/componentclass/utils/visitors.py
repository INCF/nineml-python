"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain


class ComponentClassVisitor(object):

    def visit(self, obj, **kwargs):
        return obj.accept_visitor(self, **kwargs)


class ComponentClassActionVisitor(ComponentClassVisitor):

    def __init__(self, require_explicit_overrides=True):
        self.require_explicit_overrides = require_explicit_overrides

    def visit_componentclass(self, component, **kwargs):
        self.action_componentclass(component, **kwargs)

        nodes = chain(component.parameters, component.ports)
        for p in nodes:
            p.accept_visitor(self, **kwargs)

        if component.dynamics:
            component.dynamics.accept_visitor(self, **kwargs)

        for subnode in component.subnodes.values():
            subnode.accept_visitor(self, **kwargs)

    def visit_parameter(self, parameter, **kwargs):
        self.action_parameter(parameter, **kwargs)

    def visit_alias(self, alias, **kwargs):
        self.action_alias(alias, **kwargs)

    def check_pass(self):
        if self.require_explicit_overrides:
            assert False, ("There is an overriding function missing from {}"
                           .format(self.__class__.__name__))
        else:
            pass

    # To be overridden:
    def action_componentclass(self, component, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.check_pass()
