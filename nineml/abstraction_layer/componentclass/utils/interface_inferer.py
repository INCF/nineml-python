import itertools
from .visitors import ComponentClassActionVisitor
from ...expressions.utils import get_reserved_and_builtin_symbols


class InterfaceInferer(ComponentClassActionVisitor):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, dynamics, incoming_port_names):
        ComponentClassActionVisitor.__init__(self,
                                             require_explicit_overrides=True)

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
        self.event_out_port_names = set()

        self.visit(dynamics)

        self.free_atoms -= self.input_event_port_names
        self.free_atoms -= self.event_out_port_names
        self.parameter_names = self.free_atoms

    def _notify_atom(self, atom):
        if atom not in self.accounted_for_symbols:
            self.free_atoms.add(atom)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        for atom in alias.rhs_atoms:
            self._notify_atom(atom)
