import itertools
from .visitors import ActionVisitor
from ...expressions.utils import get_reserved_and_builtin_symbols


class InterfaceInferer(ActionVisitor):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, dynamics, incoming_port_names):
        ActionVisitor.__init__(self, require_explicit_overrides=True)

        # State Variables:
        self.state_variable_names = set()
        for regime in dynamics.regimes:
            for time_deriv in regime.time_derivatives:
                self.state_variable_names.add(time_deriv.dependent_variable)
            for transition in regime.transitions:
                for state_assignment in transition.state_assignments:
                    self.state_variable_names.add(state_assignment.lhs)

        # Which symbols can we account for:
        self.accounted_for_symbols = set(itertools.chain(
            self.state_variable_names,
            dynamics.aliases_map.keys(),
            # dynamics.constants_map.keys(),  # TODO: Need to add this
            # dynamics.random_variables_map.keys(),
            incoming_port_names,
            get_reserved_and_builtin_symbols()
        ))

        # Parameters:
        # Use visitation to collect all atoms that are not aliases and not
        # state variables

        self.free_atoms = set()
        self.input_event_port_names = set()
        self.output_event_port_names = set()

        self.visit(dynamics)

        self.free_atoms -= self.input_event_port_names
        self.free_atoms -= self.output_event_port_names
        self.parameter_names = self.free_atoms

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
    def action_eventout(self, output_event, **kwargs):  # @UnusedVariable
        self.output_event_port_names.add(output_event.port_name)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        self.input_event_port_names.add(on_event.src_port_name)

    # Atoms (possible parameters):
    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        for atom in assignment.rhs_atoms:
            self._notify_atom(atom)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        for atom in alias.rhs_atoms:
            self._notify_atom(atom)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        for atom in time_derivative.rhs_atoms:
            self._notify_atom(atom)

    def action_condition(self, condition, **kwargs):  # @UnusedVariable
        for atom in condition.rhs_atoms:
            self._notify_atom(atom)

    def action_oncondition(self, on_condition, **kwargs):
        pass