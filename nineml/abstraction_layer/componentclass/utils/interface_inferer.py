from .visitors import ComponentClassActionVisitor
from ...expressions.utils import get_reserved_and_builtin_symbols
from itertools import chain


class ComponentClassInterfaceInferer(ComponentClassActionVisitor):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, componentclass, incoming_ports):
        super(ComponentClassInterfaceInferer, self).__init__(
            require_explicit_overrides=False)
        # State Variables:
        self.state_variable_names = set()
        for regime in componentclass.regimes:
            for time_deriv in regime.time_derivatives:
                self.state_variable_names.add(time_deriv.dependent_variable)
            for transition in regime.transitions:
                for state_assignment in transition.state_assignments:
                    self.state_variable_names.add(state_assignment.lhs)

        # Which symbols can we account for:
        self.accounted_for_symbols = set(chain(
            self.state_variable_names,
            componentclass.aliases_map.keys(),
            # dynamics.constants_map.keys(),  # TODO: Need to add this
            # dynamics.random_variables_map.keys(),
            incoming_ports,
            get_reserved_and_builtin_symbols()
        ))

        # Parameters:
        # Use visitation to collect all atoms that are not aliases and not
        # state variables
        self.componentclass = componentclass
        self.declared_symbols = set(get_reserved_and_builtin_symbols())
        self.atoms = set()
        self.input_event_port_names = set()
        self.event_out_port_names = set()
        self.visit(self.componentclass)
        # Visit class and populate declared_symbols and atoms sets
        self.parameter_names = (self.atoms - self.declared_symbols -
                                set(get_reserved_and_builtin_symbols()) -
                                self.accounted_for_symbols)

    def _notify_atom(self, atom):
        self.free_atoms.add(atom)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.declared_symbols.add(alias.lhs)
        self.atoms.update(alias.rhs_atoms)


        # State Variables:
#         self.state_variable_names = set()
#         for regime in dynamicsclass.regimes:
#             for time_deriv in regime.time_derivatives:
#                 self.state_variable_names.add(time_deriv.dependent_variable)
#             for transition in regime.transitions:
#                 for state_assignment in transition.state_assignments:
#                     self.state_variable_names.add(state_assignment.lhs)
#
#         # Which symbols can we account for:
#         self.accounted_for_symbols = set(itertools.chain(
#             self.state_variable_names,
#             dynamicsclass.aliases_map.keys(),
#             # dynamics.constants_map.keys(),  # TODO: Need to add this
#             # dynamics.random_variables_map.keys(),
#             incoming_port_names,
#             get_reserved_and_builtin_symbols()
#         ))
