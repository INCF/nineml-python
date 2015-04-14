"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from collections import defaultdict
from . import PerNamespaceComponentValidator
from nineml.exceptions import NineMLRuntimeError
from ...expressions.utils import is_valid_lhs_target
from ...expressions import reserved_identifiers
from nineml.utils import assert_no_duplicates
import sympy.core.numbers


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
            self._dimensions[a.name] = sympy.sympify(a.dimension)
        for a in componentclass.attributes_with_units:
            self._dimensions[a.name] = sympy.sympify(a.units.dimension)
        self.visit(componentclass)

    def _get_dimensions(self, element):
        try:
            expr = element.rhs
        except AttributeError:  # for basic sympy expressions
            expr = element
        try:
            return self._dimensions[element.name]
        except (KeyError, AttributeError):  # for derived dimensions
            dims = self._flatten_dims(expr, element)
        try:
            self._dimensions[element.name] = dims
        except AttributeError:
            pass
        return dims

    def _flatten_dims(self, expr, element):
        if isinstance(expr, (sympy.Integer, sympy.Float)):
            dims = 1
        elif isinstance(expr, sympy.Symbol):
            if expr == sympy.Symbol('t'):  # Reserved symbol
                dims = sympy.Symbol('t')
            else:
                dims = self._get_dimensions(self.componentclass[str(expr)])
        elif isinstance(expr, sympy.Mul):
            dims = (self._flatten_dims(expr.args[0], element) *
                    self._flatten_dims(expr.args[1], element))
            if isinstance(dims, sympy.Basic):
                dims = dims.powsimp()
        elif isinstance(expr, sympy.Pow):
            exp_dims = self._flatten_dims(expr.args[1], element)
            if exp_dims != 1:
                raise NineMLRuntimeError(
                    "Exponents are required to be dimensionless arguments, "
                    "found {} ({}) in {} element : {}"
                    .format(exp_dims, expr.args[1], type(expr), expr))
            # FIXME: Probably should check that if the exponent is not an
            # integer that the base is dimensionless
            dims = (self._flatten_dims(expr.args[0], element) ** expr.args[1])
        elif isinstance(expr, sympy.Add):
            arg1_dims = self._flatten_dims(expr.args[0], element)
            arg2_dims = self._flatten_dims(expr.args[1], element)
            if arg1_dims - arg2_dims == 0:
                dims = arg1_dims
            else:
                symbol_dims = ', '.join(
                    '{}={}'.format(a, self._dimensions[str(a)])
                    for a in element.rhs_symbols)
                if element is None:
                    err_msg = ("Dimensions do not match in expression {} ({})"
                               .format(expr, symbol_dims))
                else:
                    err_msg = ("Dimensions do not match for {} '{}': {} -> "
                               "{} + {} ({})".format(
                                   element.__class__.__name__, element._name,
                                   element.rhs, arg1_dims, arg2_dims,
                                   symbol_dims))
                raise NineMLRuntimeError(err_msg)
        elif isinstance(type(expr), sympy.FunctionClass):
            arg_dims = self._flatten_dims(expr.args[0], element)
            if arg_dims != 1:
                raise NineMLRuntimeError(
                    "Function '{}' requires dimensionless arguments, found {} "
                    " ({})".format(type(expr), arg_dims, expr))
            dims = 1
        elif type(expr).__name__ in ('Pi',):
            dims = 1
        else:
            raise NotImplementedError
        return dims

    def _compare_dimensionality(self, dimension, reference, element, ref_name):
        if dimension - sympy.sympify(reference) != 0:
            raise NineMLRuntimeError(
                "Dimension of '{}', {} (from {}), does not"
                " match that declared for '{}', {} ('{}')"
                .format(element._name, dimension, element.rhs, ref_name,
                        sympy.sympify(reference), reference.name))

    def _check_boolean_expr(self, expr):
        lhs, rhs = expr.args
        lhs_dimension = self._get_dimensions(lhs)
        rhs_dimension = self._get_dimensions(rhs)
        if lhs_dimension - rhs_dimension != 0:
            raise NineMLRuntimeError(
                "LHS/RHS dimensions of boolean expression '{}' do not "
                "match ({} != {})".format(expr, lhs_dimension, rhs_dimension))

    def _check_send_port(self, port):
        element = self.componentclass[port.name]
        try:
            if element.dimension != port.dimension:
                raise NineMLRuntimeError(
                    "Send port dimension '{}' does not match connected element"
                    " '{}'".format(port.dimension.name,
                                   element.dimension.name))
        except AttributeError:  # If element doesn't have explicit dimension
            self._compare_dimensionality(self._get_dimensions(element),
                                         port.dimension, element, port.name)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self._get_dimensions(alias)  # Check if dimensions can be resolved
