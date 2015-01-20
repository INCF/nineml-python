"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.abstraction_layer.dynamics.visitors import ActionVisitor
from nineml.abstraction_layer.componentclass import ComponentClass, Parameter
from ..base import Dynamics
from ...expressions import Alias
from ..regimes import StateVariable, Regime, TimeDerivative
from ...ports import (AnalogSendPort, AnalogReceivePort, AnalogReducePort,
                      EventSendPort, EventReceivePort)
from ..transitions import (EventOut, StateAssignment, OnEvent, OnCondition,
                           Condition)


class TypesValidator(ActionVisitor):

    def __init__(self, component):
        self.visit(component)

    def action_componentclass(self, component):
        assert isinstance(component, ComponentClass)

    def action_dynamics(self, dynamics):
        assert isinstance(dynamics, Dynamics)

    def action_regime(self, regime):
        assert isinstance(regime, Regime)

    def action_statevariable(self, state_variable):
        assert isinstance(state_variable, StateVariable)

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

    def action_outputevent(self, output_event, **kwargs):  # @UnusedVariable
        assert isinstance(output_event, EventOut)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        assert isinstance(assignment, StateAssignment)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        assert isinstance(alias, Alias)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        assert isinstance(time_derivative, TimeDerivative)

    def action_condition(self, condition):
        assert isinstance(condition, Condition)

    def action_oncondition(self, on_condition):
        assert isinstance(on_condition, OnCondition)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        assert isinstance(on_event, OnEvent)
