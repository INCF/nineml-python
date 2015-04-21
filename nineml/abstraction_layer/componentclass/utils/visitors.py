"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...expressions import reserved_identifiers


class ComponentVisitor(object):

    def visit(self, obj, **kwargs):
        return obj.accept_visitor(self, **kwargs)


class ComponentActionVisitor(ComponentVisitor):

    def __init__(self, require_explicit_overrides=True):
        self.require_explicit_overrides = require_explicit_overrides
        self._scopes = []

    def visit_componentclass(self, component_class, **kwargs):
        self.action_componentclass(component_class, **kwargs)
        self._scopes.append(component_class)
        for p in component_class:
            p.accept_visitor(self, **kwargs)
        popped = self._scopes.pop()
        assert popped is component_class

    def visit_parameter(self, parameter, **kwargs):
        self.action_parameter(parameter, **kwargs)

    def visit_alias(self, alias, **kwargs):
        self.action_alias(alias, **kwargs)

    def visit_constant(self, constant, **kwargs):
        self.action_constant(constant, **kwargs)

    def visit_randomvariable(self, random_variable, **kwargs):
        self.action_randomvariable(random_variable, **kwargs)
        self.visit(random_variable.distribution, **kwargs)

    def visit_randomdistribution(self, random_distribution, **kwargs):
        self.action_randomdistribution(random_distribution, **kwargs)

    def check_pass(self):
        if self.require_explicit_overrides:
            assert False, ("There is an overriding function missing from {}"
                           .format(self.__class__.__name__))
        else:
            pass

    # To be overridden:
    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_randomdistribution(self, random_distribution, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()


class ComponentRequiredDefinitions(object):
    """
    Gets lists of required parameters, states, ports, random variables,
    constants and expressions (in resolved order of execution).
    """

    def __init__(self, component_class, expressions):
        # Expression can either be a single expression or an iterable of
        # expressions
        self.parameters = set()
        self.ports = set()
        self.constants = set()
        self.random_variables = set()
        self.expressions = list()
        self._required_stack = []
        self._push_required_symbols(expressions)
        self._componentclass = component_class
        self.visit(component_class)

    def __repr__(self):
        return ("Parameters: {}\nPorts: {}\nConstants: {}\nAliases:\n{}"
                .format(', '.join(self.parameter_names),
                        ', '.join(self.port_names),
                        ', '.join(self.constant_names),
                        ', '.join(self.expression_names)))

    def _push_required_symbols(self, expression):
        required_atoms = set()
        try:
            for expr in expression:
                required_atoms.update(expr.rhs_atoms)
        except TypeError:
            required_atoms.update(expression.rhs_atoms)
        # Strip builtin symbols from required atoms
        required_atoms.difference_update(reserved_identifiers)
        self._required_stack.append(required_atoms)

    def _is_required(self, element):
        return element.name in self._required_stack[-1]

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if self._is_required(parameter):
            self.parameters.add(parameter)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        if self._is_required(port):
            self.ports.add(port)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        if self._is_required(port):
            self.ports.add(port)

    def action_constants(self, constant, **kwargs):  # @UnusedVariable
        if self._is_required(constant):
            self.constants.add(constant)

    def action_randomvariable(self, random_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        if self._is_required(random_variable):
            self.constants.add(random_variable)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if (self._is_required(alias) and
                alias.name not in (e.name for e in self.expressions)):
            # Since aliases may be dependent on other aliases/piecewises the
            # order they are executed is important so we make sure their
            # dependencies are added first
            self._push_required_symbols(alias)
            self.visit(self._componentclass)
            self._required_stack.pop()
            self.expressions.append(alias)

    @property
    def parameter_names(self):
        return (p.name for p in self.parameters)

    @property
    def port_names(self):
        return (p.name for p in self.ports)

    @property
    def constant_names(self):
        return (c.name for c in self.constants)

    @property
    def expression_names(self):
        return (e.name for e in self.expressions)


class ComponentElementFinder(ComponentActionVisitor):

    def __init__(self, element):
        super(ComponentElementFinder, self).__init__(
            require_explicit_overrides=True)
        self.element = element

    def found_in(self, component_class):
        self.found = False
        self.visit(component_class)
        return self.found

    def _found(self):
        self.found = True

    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        pass

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if self.element is parameter:
            self._found()

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if self.element is alias:
            self._found()

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        if self.element is constant:
            self._found()
