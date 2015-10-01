"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLRuntimeError, NineMLDimensionError
from nineml.abstraction.expressions.utils import is_valid_lhs_target
from nineml.abstraction.expressions import reserved_identifiers
from nineml.utils import assert_no_duplicates
import operator
import sympy
from sympy import sympify
from nineml.base import SendPortBase
from nineml.abstraction.expressions import Expression
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
from .base import BaseValidator


class AliasesAreNotRecursiveComponentValidator(BaseValidator):

    """Check that aliases are not self-referential"""

    def __init__(self, component_class):
        BaseValidator.__init__(
            self, require_explicit_overrides=False)
        self.visit(component_class)

    def action_componentclass(self, component_class):

        unresolved_aliases = dict((a.lhs, a) for a in component_class.aliases)

        def alias_contains_unresolved_symbols(alias):
            unresolved = [sym for sym in alias.rhs_symbol_names
                          if sym in unresolved_aliases]
            return len(unresolved) != 0

        def get_resolved_aliases():
            return [alias for alias in unresolved_aliases.values()
                    if not alias_contains_unresolved_symbols(alias)]

        while(unresolved_aliases):
            resolved_aliases = get_resolved_aliases()
            if resolved_aliases:
                for r in resolved_aliases:
                    del unresolved_aliases[r.lhs]

            else:
                raise NineMLRuntimeError(
                    "Unable to resolve all aliases, you may have a recursion "
                    "issue. Remaining Aliases: {}".format(
                        ','.join(unresolved_aliases.keys())))


class NoUnresolvedSymbolsComponentValidator(BaseValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """

    def __init__(self, component_class):
        BaseValidator.__init__(
            self, require_explicit_overrides=False)

        self.available_symbols = []
        self.aliases = []
        self.time_derivatives = []
        self.state_assignments = []
        self.component_class = component_class
        self.visit(component_class)

        # Check Aliases:
        for alias in self.aliases:
            for rhs_atom in alias.rhs_symbol_names:
                if rhs_atom in reserved_identifiers:
                    continue
                if rhs_atom not in self.available_symbols:
                    raise NineMLRuntimeError(
                        "Unresolved Symbol in Alias: {} [{}]"
                        .format(rhs_atom, alias))

        # Check TimeDerivatives:
        for timederivative in self.time_derivatives:
            for rhs_atom in timederivative.rhs_symbol_names:
                if (rhs_atom not in self.available_symbols and
                        rhs_atom not in reserved_identifiers):
                    try:
                        raise NineMLRuntimeError(
                            "Unresolved Symbol in Time Derivative: {} [{}]"
                            .format(rhs_atom, timederivative))
                    except:
                        td = list(timederivative.rhs_symbol_names)
                        print td

        # Check StateAssignments
        for state_assignment in self.state_assignments:
            for rhs_atom in state_assignment.rhs_symbol_names:
                if (rhs_atom not in self.available_symbols and
                        rhs_atom not in reserved_identifiers):
                    raise NineMLRuntimeError(
                        'Unresolved Symbol in Assignment: {} [{}]'
                        .format(rhs_atom, state_assignment))

    def add_symbol(self, symbol):
        if symbol in self.available_symbols:
            raise NineMLRuntimeError(
                "Duplicate Symbol '{}' found".format(symbol))
        self.available_symbols.append(symbol)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias in self.component_class.aliases:
            self.add_symbol(symbol=alias.lhs)
            self.aliases.append(alias)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(symbol=parameter.name)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(constant.name)


class NoDuplicatedObjectsComponentValidator(BaseValidator):

    def __init__(self, component_class):
        BaseValidator.__init__(self, require_explicit_overrides=True)
        self.all_objects = list()
        self.visit(component_class)
        assert_no_duplicates(self.all_objects)

    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(component_class)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.all_objects.append(parameter)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.all_objects.append(alias)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.all_objects.append(constant)


class CheckNoLHSAssignmentsToMathsNamespaceComponentValidator(BaseValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """

    def __init__(self, component_class):
        BaseValidator.__init__(
            self, require_explicit_overrides=False)

        self.visit(component_class)

    def check_lhssymbol_is_valid(self, symbol):
        assert isinstance(symbol, basestring)

        if not is_valid_lhs_target(symbol):
            err = 'Symbol: %s found on left-hand-side of an equation'
            raise NineMLRuntimeError(err)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(parameter.name)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(alias.lhs)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(constant.name)


class DimensionalityComponentValidator(BaseValidator):

    def __init__(self, component_class):
        BaseValidator.__init__(self, require_explicit_overrides=False)
        self.component_class = component_class
        self._dimensions = {}
        # Insert declared dimensions into dimensionality database
        for e in component_class.elements:
            if not isinstance(e, SendPortBase):
                try:
                    self._dimensions[e] = sympify(e.dimension)
                except AttributeError:
                    pass
                try:
                    self._dimensions[e] = sympify(e.units.dimension)
                except AttributeError:
                    pass
        self.visit(component_class)

    def _get_dimensions(self, element):
        if isinstance(element, (sympy.Symbol, basestring)):
            if element == sympy.Symbol('t'):  # Reserved symbol 't'
                return sympy.Symbol('t')  # representation of the time dim.
            name = Expression.symbol_to_str(element)
            element = None
            for scope in reversed(self._scopes):
                try:
                    element = scope.element(name)
                except KeyError:
                    pass
            if element is None:
                raise NineMLRuntimeError(
                    "Did not find '{}' in '{}' dynamics class (scopes: {})"
                    .format(name, self.component_class.name,
                            list(reversed(self._scopes))))
        try:
            expr = element.rhs
        except AttributeError:  # for basic sympy expressions
            expr = element
        try:
            return self._dimensions[element]
        except (KeyError, AttributeError):  # for derived dimensions
            dims = self._flatten_dims(expr, element)
        try:
            self._dimensions[element] = dims
        except AttributeError:
            pass
        return dims

    def _flatten_dims(self, expr, element):
        if isinstance(expr, (sympy.Integer, sympy.Float, int, float)):
            dims = 1
        elif isinstance(expr, (BooleanTrue, BooleanFalse)):
            dims = 0
        elif isinstance(expr, sympy.Symbol):
            dims = self._get_dimensions(expr)
        elif isinstance(expr, sympy.Mul):
            dims = reduce(operator.mul,
                          (self._flatten_dims(a, element) for a in expr.args))
            if isinstance(dims, sympy.Basic):
                dims = dims.powsimp()
        elif isinstance(expr, sympy.Pow):
            base = expr.args[0]
            exponent = expr.args[1]
            exp_dims = self._flatten_dims(exponent, element)
            if exp_dims != 1:
                raise NineMLDimensionError(self._construct_error_message(
                    "Exponents are required to be dimensionless arguments,"
                    " which was not the case in", exp_dims, expr, element))
            base_dims = self._flatten_dims(base, element)
            if base_dims != 1:
                if not isinstance(exponent, (sympy.Integer, int,
                                             sympy.numbers.NegativeOne)):
                    raise NineMLDimensionError(self._construct_error_message(
                        "Integer exponents are required for non-dimensionless "
                        "bases, which was not the case in", exp_dims, expr,
                        element))
            dims = (self._flatten_dims(base, element) ** exponent)
        elif isinstance(expr, sympy.Add):
            dims = None
            for arg in expr.args:
                arg_dims = self._flatten_dims(arg, element)
                if dims is None:
                    dims = arg_dims
                elif arg_dims - dims != 0:
                    raise NineMLDimensionError(self._construct_error_message(
                        "Dimensions do not match within",
                        ' + '.join(str(self._flatten_dims(a, element))
                                   for a in expr.args), expr, element))
        elif isinstance(expr, (sympy.GreaterThan, sympy.LessThan,
                               sympy.StrictGreaterThan, sympy.StrictLessThan)):
            lhs_dims = self._flatten_dims(expr.args[0], element)
            rhs_dims = self._flatten_dims(expr.args[1], element)
            if lhs_dims - rhs_dims != 0:
                raise NineMLDimensionError(self._construct_error_message(
                    "LHS/RHS dimensions of boolean expression",
                    lhs_dims - rhs_dims, expr, postamble="do not match"))
            dims = 0  # boolean expression
        elif isinstance(expr, (sympy.And, sympy.Or, sympy.Not)):
            for arg in expr.args:
                dims = self._flatten_dims(arg, element)
                # boolean expression == 0
                if dims != 0 and dims != 1:  # FIXME: allow dimless until bool params @IgnorePep8
                    raise NineMLDimensionError(self._construct_error_message(
                        "Logical expression provided non-boolean argument '{}'"
                        .format(arg), dims, expr))
        elif isinstance(type(expr), sympy.FunctionClass):
            for arg in expr.args:
                arg_dims = self._flatten_dims(arg, element)
                if arg_dims != 1:
                    raise NineMLDimensionError(self._construct_error_message(
                        "Dimensionless arguments required for function",
                        arg_dims, element=element, expr=arg))
            dims = 1
        elif (type(expr).__name__ in ('Pi',) or
              isinstance(expr, sympy.Rational)):
            dims = 1
        else:
            raise NotImplementedError(
                "Unrecognised type {} of expression '{}'"
                .format(type(expr), expr))
        return dims

    def _compare_dimensionality(self, dimension, reference, element, ref_name):
        if dimension - sympify(reference) != 0:
            raise NineMLDimensionError(self._construct_error_message(
                "Dimension of", dimension, element=element,
                postamble=(" match that declared for '{}', {} ('{}')".format(
                    ref_name, sympify(reference), reference.name))))

    def _check_send_port(self, port):
        element = self.component_class.element(port.name)
        try:
            if element.dimension != port.dimension:
                raise NineMLDimensionError(self._construct_error_message(
                    "Dimension of", sympify(element.dimension),
                    element=element, postamble=(
                        "does match attached send port dimension {} ('{}')"
                        .format(sympify(port.dimension),
                                port.dimension.name))))
        except AttributeError:  # If element doesn't have explicit dimension
            self._compare_dimensionality(self._get_dimensions(element),
                                         port.dimension, element, port.name)

    def _construct_error_message(self, preamble, dimension, expr=None,
                                 element=None, postamble=None):
        if expr is None:
            try:
                expr = element.rhs
                symbols = element.rhs_symbol_names
            except AttributeError:
                expr = ''
                symbols = []
        else:
            symbols = expr.free_symbols
        msg = preamble
        if element is None:
            msg += ' expression'
        else:
            msg += " {} '{}'".format(element.__class__.__name__, element._name)
        msg += ", {} [{}, with {}], ".format(
            dimension, expr, ', '.join(
                '{}={}'.format(a, self._get_dimensions(a)) for a in symbols))
        if postamble is not None:
            msg += postamble
        return msg

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self._get_dimensions(alias)
