"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from past.builtins import basestring
from nineml.exceptions import NineMLUsageError, NineMLDimensionError
from nineml.abstraction.expressions.utils import is_valid_lhs_target
from nineml.abstraction.expressions import reserved_identifiers, Expression
from nineml.base import BaseNineMLObject
import operator
import sympy
from sympy import sympify
from nineml.base import SendPortBase
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
from nineml.visitors import BaseVisitor, BaseVisitorWithContext
from functools import reduce


class AliasesAreNotRecursiveComponentValidator(BaseVisitor):

    """Check that aliases are not self-referential"""

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseVisitor.__init__(self)
        self.visit(component_class)

    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8

        unresolved_aliases = dict((a.lhs, a) for a in component_class.aliases)

        def alias_contains_unresolved_symbols(alias):
            unresolved = [sym for sym in alias.rhs_symbol_names
                          if sym in unresolved_aliases]
            return len(unresolved) != 0

        def get_resolved_aliases():
            return [alias for alias in list(unresolved_aliases.values())
                    if not alias_contains_unresolved_symbols(alias)]

        while(unresolved_aliases):
            resolved_aliases = get_resolved_aliases()
            if resolved_aliases:
                for r in resolved_aliases:
                    del unresolved_aliases[r.lhs]

            else:
                raise NineMLUsageError(
                    "Unable to resolve all aliases, you may have a recursion "
                    "issue. Remaining Aliases: {}".format(
                        ','.join(list(unresolved_aliases.keys()))))

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class NoUnresolvedSymbolsComponentValidator(BaseVisitor):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """

    def __init__(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        BaseVisitor.__init__(self)

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
                    raise NineMLUsageError(
                        "Unresolved Symbol in Alias: {} [{}]"
                        .format(rhs_atom, alias))

        # Check TimeDerivatives:
        for timederivative in self.time_derivatives:
            for rhs_atom in timederivative.rhs_symbol_names:
                if (rhs_atom not in self.available_symbols and
                        rhs_atom not in reserved_identifiers):
                    raise NineMLUsageError(
                        "Unresolved Symbol in Time Derivative: {} [{}]"
                        .format(rhs_atom, timederivative))

        # Check StateAssignments
        for state_assignment in self.state_assignments:
            for rhs_atom in state_assignment.rhs_symbol_names:
                if (rhs_atom not in self.available_symbols and
                        rhs_atom not in reserved_identifiers):
                    raise NineMLUsageError(
                        'Unresolved Symbol in Assignment: {} [{}]'
                        .format(rhs_atom, state_assignment))

    def add_symbol(self, symbol):
        if symbol in self.available_symbols:
            raise NineMLUsageError(
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

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class CheckNoLHSAssignmentsToMathsNamespaceComponentValidator(
        BaseVisitor):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseVisitor.__init__(self)

        self.visit(component_class)

    def check_lhssymbol_is_valid(self, symbol):
        assert isinstance(symbol, basestring)

        if not is_valid_lhs_target(symbol):
            err = 'Symbol: %s found on left-hand-side of an equation'
            raise NineMLUsageError(err)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(parameter.name)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(alias.lhs)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(constant.name)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class DimensionalityComponentValidator(BaseVisitorWithContext):

    _RECURSION_MAX = 450

    class DeclaredDimensionsVisitor(BaseVisitor):
        """
        Inserts declared dimensions into dimensionality dictionary
        before inferring dimensions from derived expressions
        """

        def __init__(self, component_class, as_class, **kwargs):
            BaseVisitor.__init__(self)
            self._dimensions = {}
            self.as_class = as_class
            self.visit(component_class, **kwargs)

        def default_action(self, obj, nineml_cls, **kwargs):  # @UnusedVariable
            if not isinstance(obj, SendPortBase):
                try:
                    self._dimensions[obj.id] = sympify(obj.dimension)
                except AttributeError:
                    # If element doesn't have dimension attribute
                    try:
                        self._dimensions[obj.id] = sympify(obj.units.dimension)
                    except AttributeError:
                        pass  # If element doesn't have units attribute

        @property
        def dimensions(self):
            return self._dimensions

    def __init__(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        BaseVisitorWithContext.__init__(self)
        self.component_class = component_class
        self._dimensions = self.DeclaredDimensionsVisitor(
            component_class, self.as_class, **kwargs).dimensions
        self._recursion_count = 0
        self.visit(component_class)

    def _get_dimensions(self, element):
        if isinstance(element, (sympy.Symbol, basestring)):
            if element == sympy.Symbol('t'):  # Reserved symbol 't'
                return sympy.Symbol('t')  # representation of the time dim.
            name = Expression.symbol_to_str(element)
            # Look back through the scope stack to find the referenced
            # element
            element = None
            for context in reversed(self.contexts):
                try:
                    element = context.parent.element(
                        name, child_types=context.parent_cls.nineml_children)
                except KeyError:
                    pass
            if element is None:
                raise NineMLUsageError(
                    "Did not find '{}' in '{}' dynamics class (scopes: {})"
                    .format(name, self.component_class.name,
                            list(reversed([c.parent for c in self.contexts]))))
        try:
            expr = element.rhs
        except AttributeError:  # for basic sympy expressions
            expr = element
        try:
            dims = self._dimensions[element.id]
            self._recursion_count = 0
        except (KeyError, AttributeError):  # for derived dimensions
            if self._recursion_count > self._RECURSION_MAX:
                assert False, (
                    "'{}' is not defined.\nDefined symbols:\n{}"
                    "\n\nElements:\n{}".format(
                        expr, "\n".join(
                            str(e) for e in self._dimensions.keys()),
                        "\n".join(
                            str(e) for e in self.component_class.elements(
                                child_types=(
                                    self.as_class.nineml_children)))
                    ))
            self._recursion_count += 1
            dims = self._flatten_dims(expr, element)
            self._dimensions[element.id] = dims
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
        elif isinstance(element, BaseNineMLObject):
            assert False, ("{} was not added to pre-determined dimensions"
                           .format(element))
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
        # Get the state variable or alias associated with the analog send
        # port
        element = self.component_class.element(
            port.name, child_types=self.as_class.nineml_children)
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
            msg += " {} '{}' in '{}'".format(
                element.__class__.__name__, element.key,
                self.component_class.name)
        msg += ", {} [{}, with {}], ".format(
            dimension, expr, ', '.join(
                '{}={}'.format(a, self._get_dimensions(a)) for a in symbols))
        if postamble is not None:
            msg += postamble
        return msg

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self._get_dimensions(alias)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass
