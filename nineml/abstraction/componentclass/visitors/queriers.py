from copy import copy
import sympy
from sympy import sympify
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
from sympy.functions.elementary.piecewise import ExprCondPair
from .base import ComponentActionVisitor
from ...expressions import reserved_identifiers
from nineml.units import Dimension
from nineml.abstraction.ports import SendPortBase
from nineml.abstraction.expressions import Expression
import operator


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

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        if self._is_required(constant):
            self.constants.add(constant)

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


class ComponentExpressionExtractor(ComponentActionVisitor):

    def __init__(self):
        super(ComponentExpressionExtractor, self).__init__(
            require_explicit_overrides=False)
        self.expressions = []

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.expressions.append(alias.rhs)


class ComponentDimensionResolver(ComponentActionVisitor):
    """
    Used to calculate the unit dimension of elements within a component class
    """

    reserved_symbol_dims = {sympy.Symbol('t'): sympy.Symbol('t')}

    def __init__(self, component_class):
        ComponentActionVisitor.__init__(
            self, require_explicit_overrides=False)
        self.component_class = component_class
        self._dims = {}
        # Insert declared dimensions into dimensionality database
        for a in component_class.attributes_with_dimension:
            if not isinstance(a, SendPortBase):
                self._dims[sympify(a)] = sympify(a.dimension)
        for a in component_class.attributes_with_units:
            self._dims[sympify(a)] = sympify(a.units.dimension)
        self.visit(component_class)

    def __getitem__(self, element):
        return Dimension.from_sympy(self._flatten(sympify(element)))

    def _flatten(self, expr):
        if expr in self.reserved_symbol_dims:
            return self.reserved_symbol_dims[expr]
        elif isinstance(expr, sympy.Symbol):
            try:
                dim = self._dims[expr]
            except KeyError:
                name = Expression.symbol_to_str(expr)
                element = None
                for scope in reversed(self._scopes):
                    try:
                        element = scope[name]
                    except KeyError:
                        pass
                if element is None:
                    raise KeyError(
                        "'{}' element was not found in component class '{}'"
                        .format(element.name, self.component_class.name))
                dim = self._flatten(element.rhs)
                self._dims[expr] = dim
        elif isinstance(expr, (sympy.GreaterThan, sympy.LessThan,
                               sympy.StrictGreaterThan, sympy.StrictLessThan)):
            dim = 0
        elif isinstance(expr, (BooleanTrue, BooleanFalse, sympy.And, sympy.Or,
                               sympy.Not)):
            dim = 0
        elif isinstance(expr, (sympy.Integer, sympy.Float, int, float)):
            dim = 1
        elif isinstance(type(expr), sympy.FunctionClass):
            dim = 1
        elif (type(expr).__name__ in ('Pi',) or
              isinstance(expr, sympy.Rational)):
            dim = 1
        elif isinstance(expr, sympy.Pow):
            dim = (self._flatten(expr.args[0]) ** expr.args[1])
        elif isinstance(expr, sympy.Add):
            dim = self._flatten(expr.arg[0])
        elif isinstance(expr, sympy.Piecewise):
            dim = self._flatten(expr.arg[0])
        elif isinstance(expr, ExprCondPair):
            dim = self._flatten(expr.arg[0])
        elif isinstance(expr, sympy.Mul):
            dim = reduce(
                operator.mul, (self._flatten(a) for a in expr.args))
            if isinstance(dim, sympy.Basic):
                dim = dim.powsimp()  # Simplify the expression
        else:
            assert False, "Unrecognised expression type '{}'".format(expr)
        return dim

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self._get_sympy_expr(alias)
