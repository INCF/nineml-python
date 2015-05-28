"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from collections import defaultdict
from . import PerNamespaceComponentValidator
from nineml.exceptions import NineMLRuntimeError, NineMLDimensionError
from ...expressions.utils import is_valid_lhs_target
from ...expressions import reserved_identifiers
from nineml.utils import assert_no_duplicates
import operator
import sympy
from sympy import sympify
from nineml.base import SendPortBase
from nineml.abstraction.expressions import Expression


class AliasesAreNotRecursiveComponentValidator(PerNamespaceComponentValidator):

    """Check that aliases are not self-referential"""

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)
        self.visit(componentclass)

    def action_componentclass(self, componentclass, namespace):

        unresolved_aliases = dict((a.lhs, a) for a in componentclass.aliases)

        def alias_contains_unresolved_symbols(alias):
            unresolved = [sym for sym in alias.rhs_atoms
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
                errmsg = "Unable to resolve all aliases in %s. " % namespace
                errmsg += "You may have a recursion issue."
                errmsg += ("Remaining Aliases: %s" %
                           ','.join(unresolved_aliases.keys()))
                raise NineMLRuntimeError(errmsg)


class NoUnresolvedSymbolsComponentValidator(PerNamespaceComponentValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)

        self.available_symbols = defaultdict(list)
        self.aliases = defaultdict(list)
        self.time_derivatives = defaultdict(list)
        self.state_assignments = defaultdict(list)

        self.visit(componentclass)

        # Check Aliases:
        for ns, aliases in self.aliases.iteritems():
            for alias in aliases:
                for rhs_atom in alias.rhs_atoms:
                    if rhs_atom in reserved_identifiers:
                        continue
                    if rhs_atom not in self.available_symbols[ns]:
                        err = ('Unresolved Symbol in Alias: %s [%s]' %
                               (rhs_atom, alias))
                        raise NineMLRuntimeError(err)

        # Check TimeDerivatives:
        for ns, timederivatives in self.time_derivatives.iteritems():
            for timederivative in timederivatives:
                for rhs_atom in timederivative.rhs_atoms:
                    if (rhs_atom not in self.available_symbols[ns] and
                            rhs_atom not in reserved_identifiers):
                        raise NineMLRuntimeError(
                            "Unresolved Symbol in Time Derivative: {} [{}]"
                            .format(rhs_atom, timederivative))

        # Check StateAssignments
        for ns, state_assignments in self.state_assignments.iteritems():
            for state_assignment in state_assignments:
                for rhs_atom in state_assignment.rhs_atoms:
                    if (rhs_atom not in self.available_symbols[ns] and
                            rhs_atom not in reserved_identifiers):
                        err = ('Unresolved Symbol in Assignment: %s [%s]' %
                               (rhs_atom, state_assignment))
                        raise NineMLRuntimeError(err)

    def add_symbol(self, namespace, symbol):
        if symbol in self.available_symbols[namespace]:
            err = ("Duplicate Symbol: [%s] found in namespace: %s" %
                   (symbol, namespace))
            raise NineMLRuntimeError(err)
        self.available_symbols[namespace].append(symbol)

    def action_alias(self, alias, namespace, **kwargs):  # @UnusedVariable
        self.add_symbol(namespace=namespace, symbol=alias.lhs)
        self.aliases[namespace].append(alias)

    def action_parameter(self, parameter, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(namespace=namespace, symbol=parameter.name)

    def action_constant(self, constant, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(namespace, constant.name)


class NoDuplicatedObjectsComponentValidator(PerNamespaceComponentValidator):

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=True)
        self.all_objects = list()
        self.visit(componentclass)
        assert_no_duplicates(self.all_objects)

    def action_componentclass(self, componentclass, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(componentclass)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.all_objects.append(parameter)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.all_objects.append(alias)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.all_objects.append(constant)


class CheckNoLHSAssignmentsToMathsNamespaceComponentValidator(
        PerNamespaceComponentValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)

        self.visit(componentclass)

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


class DimensionalityComponentValidator(PerNamespaceComponentValidator):

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)
        self.componentclass = componentclass
        self._dimensions = {}
        # Insert declared dimensions into dimensionality database
        for a in componentclass.attributes_with_dimension:
            if not isinstance(a, SendPortBase):
                self._dimensions[a] = sympify(a.dimension)
        for a in componentclass.attributes_with_units:
            self._dimensions[a] = sympify(a.units.dimension)
        self.visit(componentclass)

    def _get_dimensions(self, element):
        if isinstance(element, (sympy.Symbol, basestring)):
            if element == sympy.Symbol('t'):  # Reserved symbol 't'
                return sympy.Symbol('t')  # representation of the time dim.
            element = self.componentclass[Expression.symbol_to_str(element)]
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
        elif isinstance(expr, sympy.Symbol):
            dims = self._get_dimensions(expr)
        elif isinstance(expr, sympy.Mul):
            dims = reduce(operator.mul,
                          (self._flatten_dims(a, element) for a in expr.args))
            if isinstance(dims, sympy.Basic):
                dims = dims.powsimp()
        elif isinstance(expr, sympy.Pow):
            exp_dims = self._flatten_dims(expr.args[1], element)
            if exp_dims != 1:
                raise NineMLDimensionError(self._construct_error_message(
                    "Exponents are required to be dimensionless arguments,"
                    " which was not the case in", exp_dims, expr, element))
            # FIXME: Probably should check that if the exponent is not an
            # integer that the base is dimensionless
            dims = (self._flatten_dims(expr.args[0], element) ** expr.args[1])
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
                    lhs_dims - rhs_dims, expr,
                    postamble="do not match"))
            dims = 0  # boolean expression
        elif isinstance(expr, (sympy.And, sympy.Or, sympy.Not)):
            for arg in expr.args:
                dims = self._flatten_dims(arg, element)
                if dims != 0:  # boolean expression == 0
                    raise NineMLDimensionError(self._construct_error_message(
                        "Logical expression provided non-boolean argument '{}'"
                        .format(arg), dims, expr))
        elif isinstance(type(expr), sympy.FunctionClass):
            arg_dims = self._flatten_dims(expr.args[0], element)
            if arg_dims != 1:
                raise NineMLDimensionError(self._construct_error_message(
                    "Dimensionless arguments required for function",
                    arg_dims, element=element, expr=expr))
            dims = 1
        elif type(expr).__name__ in ('Pi',):
            dims = 1
        else:
            raise NotImplementedError
        return dims

    def _compare_dimensionality(self, dimension, reference, element, ref_name):
        if dimension - sympify(reference) != 0:
            raise NineMLDimensionError(self._construct_error_message(
                "Dimension of", dimension, element=element,
                postamble=(" match that declared for '{}', {} ('{}')".format(
                    ref_name, sympify(reference), reference.name))))

    def _check_send_port(self, port):
        element = self.componentclass[port.name]
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
                symbols = element.rhs_symbols
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
        self._get_dimensions(alias)  # Check if dimensions can be resolved
