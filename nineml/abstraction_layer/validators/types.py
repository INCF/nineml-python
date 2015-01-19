"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.abstraction_layer.dynamics.visitors import ActionVisitor
from nineml.abstraction_layer.components import Parameter
from nineml.abstraction_layer.dynamics import component as al


class ComponentValidatorTypes(ActionVisitor):

    def __init__(self, component):
        self.visit(component)

    def action_componentclass(self, component):
        assert isinstance(component, al.ComponentClass)

    def action_dynamics(self, dynamics):
        assert isinstance(dynamics, al.Dynamics)

    def action_regime(self, regime):
        assert isinstance(regime, al.Regime)

    def action_statevariable(self, state_variable):
        assert isinstance(state_variable, al.StateVariable)

    def action_parameter(self, parameter):
        assert isinstance(parameter, Parameter), \
                                      "%s != %s" % (type(parameter), Parameter)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, al.AnalogSendPort)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, al.AnalogReceivePort)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, al.AnalogReducePort)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, al.EventSendPort)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        assert isinstance(port, al.EventReceivePort)

    def action_outputevent(self, output_event, **kwargs):  # @UnusedVariable
        assert isinstance(output_event, al.EventOut)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        assert isinstance(assignment, al.StateAssignment)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        assert isinstance(alias, al.Alias)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        assert isinstance(time_derivative, al.TimeDerivative)

    def action_condition(self, condition):
        assert isinstance(condition, al.Condition)

    def action_oncondition(self, on_condition):
        assert isinstance(on_condition, al.OnCondition)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        assert isinstance(on_event, al.OnEvent)
