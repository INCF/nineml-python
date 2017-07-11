from copy import copy
from collections import defaultdict
from itertools import chain
import sympy
from sympy import sympify
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
from sympy.functions.elementary.piecewise import ExprCondPair
from .base import ComponentActionVisitor
from ...expressions import reserved_identifiers
from nineml.units import Dimension
from nineml.abstraction.ports import SendPortBase
from nineml.abstraction.expressions import Expression
from nineml.exceptions import NineMLNameError
from nineml.base import BaseNineMLVisitor
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
            self.visit(self.component_class)
            self._required_stack.pop()
            self.expressions.append(alias)

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
        if self.element == parameter:
            self._found()

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if self.element == alias:
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

    def dimension_of(self, element):
        if isinstance(element, basestring):
            element = self.component_class.element(
                element, class_map=self.class_to_visit.class_to_member)
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

    def _find_element(self, sym):
        name = Expression.symbol_to_str(sym)
        element = None
        for scope in reversed(self._scopes):
            try:
                element = scope.element(
                    name, class_map=self.class_to_visit.class_to_member)
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
            element = self._find_element(sym)
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

    def action_alias(self, alias):
        self._flatten(alias)


class ComponentExpandExpressionsQuerier(BaseNineMLVisitor):
    """
    A querier that expands all mathematical expressions into terms of inputs,
    to the component class (e.g. analog receive/reduce ports and parameters),
    constants and reserved identifiers, removing all aliases except ones that
    map directly to outputs.

    Parameters
    ----------
    component_class : ComponentClass
        The component class to expand the expressions of
    new_name : str
        The name for the expanded class
    """

    def __init__(self, component_class):
        super(ComponentExpandExpressionsQuerier, self).__init__()
        self.component_class = component_class
        self.expanded_exprs = {}
        self.expanded_regimes = {}
        self.inputs = list(reserved_identifiers) + [
            sympy.Symbol(n) for n in chain(
                component_class.parameter_names,
                component_class.analog_receive_port_names,
                component_class.analog_reduce_port_names,
                component_class.constant_names)]
        self.visit(component_class)

    @property
    def expanded(self):
        return self._expanded

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.expand(alias)

    def expand(self, expr):
        # Get key to store the expression under. Aliases that are not part of
        # a regime use a key == None
        key = self.conext_key + expr.key
        try:
            return self.expanded_exprs[key]
        except KeyError:
            expanded_expr = expr.clone()
            for sym in expr.rhs_symbols:
                # Expand all symbols that are not inputs to the Dynamics class
                if sym not in self.inputs:
                    
                    expanded_expr.rhs.subs(sym, self.expand(sym))
            expanded_expr.simplify()
            self.expanded_exprs[key] = expanded_expr
            return expanded_expr
        except AttributeError:
            raise
