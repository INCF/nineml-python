from ...componentclass.utils import ComponentClassInterfaceInferer
from .visitors import DynamicsClassActionVisitor


class DynamicsClassInterfaceInferer(DynamicsClassActionVisitor,
                                    ComponentClassInterfaceInferer):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, dynamicsclass, incoming_ports):
        self.state_variable_names = set()
        super(DynamicsClassInterfaceInferer, self).__init__(dynamicsclass, incoming_ports)

    def action_statevariable(self, state_variable):
        self.declared_symbols.add(state_variable.name)

    def action_eventout(self, event_out):
        self.event_out_port_names.add(event_out.port_name)

    def action_onevent(self, on_event):
        self.input_event_port_names.add(on_event.src_port_name)

    def action_analogreceiveport(self, analog_receive_port):
        self.declared_symbols.add(analog_receive_port.name)

    def action_analogreduceport(self, analog_reduce_port):
        self.declared_symbols.add(analog_reduce_port.name)

    def action_assignment(self, assignment):
        self.state_variable_names.add(assignment.lhs)
        self.atoms.update(assignment.rhs_atoms)

    def action_timederivative(self, time_derivative):
        self.state_variable_names.add(time_derivative.dependent_variable)
        self.atoms.update(time_derivative.rhs_atoms)

    def action_condition(self, condition):
        self.atoms.update(condition.rhs_atoms)
