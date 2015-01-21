import itertools
from ...componentclass.utils import InterfaceInferer
from .visitors import DynamicsClassActionVisitor
from ...expressions.utils import get_reserved_and_builtin_symbols


class InterfaceInferer(DynamicsClassActionVisitor, InterfaceInferer):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def action_dynamics(self, dynamics, **kwargs):
        pass

    def action_regime(self, regime, **kwargs):
        pass

    def action_statevariable(self, state_variable, **kwargs):
        pass

    def _notify_atom(self, atom):
        if atom not in self.accounted_for_symbols:
            self.free_atoms.add(atom)

    # Events:
    def action_eventout(self, event_out, **kwargs):  # @UnusedVariable
        self.event_out_port_names.add(event_out.port_name)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        self.input_event_port_names.add(on_event.src_port_name)

    # Atoms (possible parameters):
    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        for atom in assignment.rhs_atoms:
            self._notify_atom(atom)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        for atom in time_derivative.rhs_atoms:
            self._notify_atom(atom)

    def action_condition(self, condition, **kwargs):  # @UnusedVariable
        for atom in condition.rhs_atoms:
            self._notify_atom(atom)

    def action_oncondition(self, on_condition, **kwargs):
        pass
