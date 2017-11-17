from past.builtins import basestring
from copy import copy
import sympy
from sympy import sympify
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
from sympy.functions.elementary.piecewise import ExprCondPair
from ...expressions import reserved_identifiers
from nineml.visitors import BaseVisitor, BaseVisitorWithContext
from nineml.units import Dimension
from nineml.abstraction.ports import SendPortBase
from nineml.abstraction.expressions import Expression
from nineml.exceptions import NineMLNameError
import operator
from functools import reduce


class ComponentClassInterfaceInferer(BaseVisitor):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, component_class):
        super(ComponentClassInterfaceInferer, self).__init__()
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

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class ComponentRequiredDefinitions(BaseVisitor):
    """
    Gets lists of required parameters, states, ports, random variables,
    constants and expressions (in resolved order of execution).
    """

    def __init__(self, component_class, expressions):
        BaseVisitor.__init__(self)
        # Expression can either be a single expression or an iterable of
        # expressions
        self.parameters = []
        self.ports = []
        self.constants = []
        self.random_variables = []
        self.expressions = []
        self._required_stack = []
        self._push_required_symbols(expressions)
        self.component_class = component_class
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
                try:
                    required_atoms.update(expr.rhs_atoms)
                except AttributeError:  # If a output port instead of expr
                    required_atoms.add(expr.name)
        except TypeError:
            required_atoms.update(expression.rhs_atoms)
        # Strip builtin symbols from required atoms
        required_atoms.difference_update(reserved_identifiers)
        self._required_stack.append(required_atoms)

    def _is_required(self, element):
        return element.name in self._required_stack[-1]

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if self._is_required(parameter):
            self.parameters.append(parameter)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        if self._is_required(port):
            self.ports.append(port)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        if self._is_required(port):
            self.ports.append(port)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        if self._is_required(constant):
            self.constants.append(constant)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if (self._is_required(alias) and
                alias.name not in (e.name for e in self.expressions)):
            # Since aliases may be dependent on other aliases/piecewises the
            # order they are executed is important so we make sure their
            # dependencies are added first
            self._push_required_symbols(alias)
            self.visit(self.component_class)
            self._required_stack.pop()
            self.expressions.append(alias)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass

    @property
    def parameter_names(self):
        return (p.name for p in self.parameters)

    @property
    def port_names(self):
        return (p.name for p in self.ports)

    @property
    def random_variable_names(self):
        return (rv.name for rv in self.random_variables)

    @property
    def constant_names(self):
        return (c.name for c in self.constants)

    @property
    def expression_names(self):
        return (e.name for e in self.expressions)


class ComponentExpressionExtractor(BaseVisitor):

    def __init__(self):
        super(ComponentExpressionExtractor, self).__init__()
        self.expressions = []

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.expressions.append(alias.rhs)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class ComponentDimensionResolver(BaseVisitorWithContext):
    """
    Used to calculate the unit dimension of elements within a component class
    """

    reserved_symbol_dims = {sympy.Symbol('t'): sympy.Symbol('t')}

    def __init__(self, component_class):
        super(ComponentDimensionResolver, self).__init__()
        self.component_class = component_class
        self._dims = {}
        # Insert declared dimensions into dimensionality database
        for a in component_class.attributes_with_dimension:
            if not isinstance(a, SendPortBase):
                self._dims[sympify(a)] = sympify(a.dimension)
        for a in component_class.attributes_with_units:
            self._dims[sympify(a)] = sympify(a.units.dimension)
        self.visit(component_class)

    @property
    def base_nineml_children(self):
        return self.as_class.nineml_children

    def dimension_of(self, element):
        if isinstance(element, basestring):
            element = self.component_class.element(
                element, child_types=self.base_nineml_children)
        return Dimension.from_sympy(self._flatten(element))

    def _flatten(self, expr, **kwargs):  # @UnusedVariable
        expr = sympify(expr)
        if expr in self.reserved_symbol_dims:
            flattened = self._flatten_reserved(expr, **kwargs)
        elif isinstance(expr, sympy.Symbol):
            flattened = self._flatten_symbol(expr, **kwargs)
        elif isinstance(expr, (sympy.GreaterThan, sympy.LessThan,
                               sympy.StrictGreaterThan, sympy.StrictLessThan,
                               BooleanTrue, BooleanFalse, sympy.And, sympy.Or,
                               sympy.Not)):
            flattened = self._flatten_boolean(expr, **kwargs)
        elif (isinstance(expr, (sympy.Integer, sympy.Float, int, float,
                                sympy.Rational)) or
              type(expr).__name__ in ('Pi',)):
            flattened = self._flatten_constant(expr, **kwargs)
        elif isinstance(expr, sympy.Pow):
            flattened = self._flatten_power(expr, **kwargs)
        elif isinstance(expr, (sympy.Add, sympy.Piecewise, ExprCondPair)):
            flattened = self._flatten_matching(expr, **kwargs)
        elif isinstance(type(expr), sympy.FunctionClass):
            flattened = self._flatten_function(expr, **kwargs)
        elif isinstance(expr, sympy.Mul):
            flattened = self._flatten_multiplied(expr, **kwargs)
        else:
            assert False, "Unrecognised expression type '{}'".format(expr)
        return flattened

    def find_element(self, sym):
        name = Expression.symbol_to_str(sym)
        element = None
        for context in reversed(self.contexts):
            try:
                element = context.parent.element(
                    name, child_types=context.parent_cls.nineml_children)
            except KeyError:
                pass
        if element is None:
            raise NineMLNameError(
                "'{}' element was not found in component class '{}'"
                .format(sym, self.component_class.name))
        return element

    def _flatten_symbol(self, sym):
        try:
            flattened = self._dims[sym]
        except KeyError:
            element = self.find_element(sym)
            flattened = self._flatten(element.rhs)
            self._dims[sym] = flattened
        return flattened

    def _flatten_boolean(self, expr, **kwargs):  # @UnusedVariable
        return 0

    def _flatten_constant(self, expr, **kwargs):  # @UnusedVariable
        return 1

    def _flatten_function(self, expr, **kwargs):  # @UnusedVariable
        return 1

    def _flatten_matching(self, expr, **kwargs):  # @UnusedVariable
        return self._flatten(expr.args[0])

    def _flatten_multiplied(self, expr, **kwargs):  # @UnusedVariable
        flattened = reduce(operator.mul, (self._flatten(a) for a in expr.args))
        if isinstance(flattened, sympy.Basic):
            flattened = flattened.powsimp()  # Simplify the expression
        return flattened

    def _flatten_power(self, expr, **kwargs):  # @UnusedVariable
        return (self._flatten(expr.args[0]) ** expr.args[1])

    def _flatten_reserved(self, expr, **kwargs):  # @UnusedVariable
        return self.reserved_symbol_dims[expr]

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self._flatten(alias)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass
