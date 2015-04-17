from copy import copy
from .visitors import ComponentActionVisitor
from ...expressions import reserved_identifiers


class ComponentClassInterfaceInferer(ComponentActionVisitor):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, component_class):
        super(ComponentClassInterfaceInferer, self).__init__(
            require_explicit_overrides=False)
        # Parameters:
        # Use visitation to collect all atoms that are not aliases and not
        # state variables
        self.component_class = component_class
        self.declared_symbols = copy(reserved_identifiers)
        self.atoms = set()
        self.input_event_port_names = set()
        self.event_out_port_names = set()
        self.visit(self.component_class)
        # Visit class and populate declared_symbols and atoms sets
        self.parameter_names = self.atoms - self.declared_symbols

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.declared_symbols.add(alias.lhs)
        self.atoms.update(alias.rhs_atoms)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.declared_symbols.add(constant.name)

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.declared_symbols.add(randomvariable.name)

    def action_randomdistribution(self, random_distribution, **kwargs):  # @UnusedVariable @IgnorePep8
        for var in random_distribution.parameters.itervalues():
            if isinstance(var, basestring):
                self.atoms.update(var)
