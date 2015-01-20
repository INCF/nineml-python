"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...dynamics.visitors import ActionVisitor
from ...dynamics.regimes import Regime, StateVariable, TimeDerivative
from ...dynamics.transitions import (EventOut, StateAssignment, Trigger,
                                     OnCondition, OnEvent)
from nineml.abstraction_layer.componentclass.base import ComponentClass, Parameter
from ...expressions import Alias
from ...ports import (AnalogSendPort, AnalogReceivePort, AnalogReducePort,
                      EventSendPort, EventReceivePort)
from ...dynamics.base import Dynamics


class TypesValidator(ActionVisitor):

    def __init__(self, component):
        super(TypesValidator, self).__init__()
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
        assert (isinstance(parameter, Parameter),
                "{} != {}".format(type(parameter), Parameter))

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, AnalogSendPort)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, AnalogReceivePort)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, AnalogReducePort)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, EventSendPort)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, EventReceivePort)

    def action_eventout(self, event_out, **kwargs):  # @UnusedVariable
        assert isinstance(event_out, EventOut)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        assert isinstance(assignment, StateAssignment)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        assert isinstance(alias, Alias)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        assert isinstance(time_derivative, TimeDerivative)

    def action_condition(self, trigger):
        assert isinstance(trigger, Trigger)

    def action_oncondition(self, on_condition):
        assert isinstance(on_condition, OnCondition)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        assert isinstance(on_event, OnEvent)
