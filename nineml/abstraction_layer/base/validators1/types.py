"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.abstraction_layer.dynamics.visitors import ActionVisitor
from nineml.abstraction_layer.componentclass import ComponentClass, Parameter
from ...expressions import Alias
from ...ports import (AnalogSendPort, AnalogReceivePort, AnalogReducePort,
                      EventSendPort, EventReceivePort)


class TypesValidator(ActionVisitor):

    def __init__(self, component):
        self.visit(component)

    def action_componentclass(self, component):
        assert isinstance(component, ComponentClass)

    def action_parameter(self, parameter):
        assert isinstance(parameter, Parameter)

    def action_angsendport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, AnalogSendPort)

    def action_angreceiveport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, AnalogReceivePort)

    def action_angreduceport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, AnalogReducePort)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, EventSendPort)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, EventReceivePort)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        assert isinstance(alias, Alias)
