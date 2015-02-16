"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLRuntimeError
from .visitors import ComponentActionVisitor
import re


class ComponentModifier(object):

    """Utility classes for modifying components"""

    pass


class ComponentRenameIdentiferModifier(ComponentActionVisitor):

    def __init__(self, componentclass, from_name, to_name):
        super(ComponentRenameIdentiferModifier, self).__init__(
            self, require_explicit_overrides=False)
        self.from_name = from_name
        self.to_name = to_name
        self._regex = re.compile(r'(?<!\w){}(?!\w)'.format(from_name))
        self._found_lhs = False
        self.visit(componentclass)
        if not self._found_lhs:
            raise NineMLRuntimeError(
                "Did not find identifier '{}' definition in component class"
                .format(self.from_name))

    def _sub_into_rhs(self, rhs):
        return self._regex.sub(self.to_name, rhs)

    def _rename_lhs(self, obj):
        if obj.name == self.from_name:
            obj.name = self.to_name
            self._found_lhs = True

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self._rename_lhs(parameter)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self._rename_lhs(alias)
        alias._rhs = self._sub_into_rhs(alias._rhs)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self._rename_lhs(constant)

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        self._rename_lhs(randomvariable)

    def action_piecewise(self, piecewise, **kwargs):  # @UnusedVariable
        self._rename_lhs(piecewise)
        for piece in piecewise.pieces:
            piece._rhs = self._sub_into_rhs(piece._rhs)
        piecewise.otherwise._rhs = self._sub_into_rhs(piecewise.otherwise._rhs)
