import unittest
from nineml.abstraction.componentclass.visitors.validators.general import (DimensionalityComponentValidator, CheckNoLHSAssignmentsToMathsNamespaceComponentValidator, NoUnresolvedSymbolsComponentValidator)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLDimensionError, NineMLRuntimeError)


class TestDimensionalityComponentValidatorExceptions(unittest.TestCase):

    def test__get_dimensions_ninemlruntimeerror(self):
        """
        line #: 208
        message: Did not find '{}' in '{}' dynamics class (scopes: {})

        context:
        --------
    def _get_dimensions(self, element):
        if isinstance(element, (sympy.Symbol, basestring)):
            if element == sympy.Symbol('t'):  # Reserved symbol 't'
                return sympy.Symbol('t')  # representation of the time dim.
            name = Expression.symbol_to_str(element)
            # Look back through the scope stack to find the referenced
            # element
            element = None
            for scope in reversed(self._scopes):
                try:
                    element = scope.element(
                        name,
                        class_map=self.class_to_visit.class_to_member)
                except KeyError:
                    pass
            if element is None:
        """

        dimensionalitycomponentvalidator = next(instances_of_all_types['DimensionalityComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            dimensionalitycomponentvalidator._get_dimensions,
            element=None)

    def test__compare_dimensionality_ninemldimensionerror(self):
        """
        line #: 314
        message: self

        context:
        --------
    def _compare_dimensionality(self, dimension, reference, element, ref_name):
        if dimension - sympify(reference) != 0:
        """

        dimensionalitycomponentvalidator = next(instances_of_all_types['DimensionalityComponentValidator'].itervalues())
        self.assertRaises(
            NineMLDimensionError,
            dimensionalitycomponentvalidator._compare_dimensionality,
            dimension=None,
            reference=None,
            element=None,
            ref_name=None)

    def test__check_send_port_ninemldimensionerror(self):
        """
        line #: 326
        message: self

        context:
        --------
    def _check_send_port(self, port):
        # Get the state variable or alias associated with the analog send
        # port
        element = self.component_class.element(
            port.name, self.class_to_visit.class_to_member)
        try:
            if element.dimension != port.dimension:
        """

        dimensionalitycomponentvalidator = next(instances_of_all_types['DimensionalityComponentValidator'].itervalues())
        self.assertRaises(
            NineMLDimensionError,
            dimensionalitycomponentvalidator._check_send_port,
            port=None)


class TestCheckNoLHSAssignmentsToMathsNamespaceComponentValidatorExceptions(unittest.TestCase):

    def test_check_lhssymbol_is_valid_ninemlruntimeerror(self):
        """
        line #: 157
        message: err

        context:
        --------
    def check_lhssymbol_is_valid(self, symbol):
        assert isinstance(symbol, basestring)

        if not is_valid_lhs_target(symbol):
            err = 'Symbol: %s found on left-hand-side of an equation'
        """

        checknolhsassignmentstomathsnamespacecomponentvalidator = next(instances_of_all_types['CheckNoLHSAssignmentsToMathsNamespaceComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            checknolhsassignmentstomathsnamespacecomponentvalidator.check_lhssymbol_is_valid,
            symbol=None)


class TestNoUnresolvedSymbolsComponentValidatorExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 78
        message: Unresolved Symbol in Alias: {} [{}]

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
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
        """

        nounresolvedsymbolscomponentvalidator = next(instances_of_all_types['NoUnresolvedSymbolsComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            nounresolvedsymbolscomponentvalidator.__init__,
            component_class=None)

    def test___init___ninemlruntimeerror2(self):
        """
        line #: 87
        message: Unresolved Symbol in Time Derivative: {} [{}]

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
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
        """

        nounresolvedsymbolscomponentvalidator = next(instances_of_all_types['NoUnresolvedSymbolsComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            nounresolvedsymbolscomponentvalidator.__init__,
            component_class=None)

    def test___init___ninemlruntimeerror3(self):
        """
        line #: 96
        message: Unresolved Symbol in Assignment: {} [{}]

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
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
                    raise NineMLRuntimeError(
                        "Unresolved Symbol in Time Derivative: {} [{}]"
                        .format(rhs_atom, timederivative))

        # Check StateAssignments
        for state_assignment in self.state_assignments:
            for rhs_atom in state_assignment.rhs_symbol_names:
                if (rhs_atom not in self.available_symbols and
                        rhs_atom not in reserved_identifiers):
        """

        nounresolvedsymbolscomponentvalidator = next(instances_of_all_types['NoUnresolvedSymbolsComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            nounresolvedsymbolscomponentvalidator.__init__,
            component_class=None)

    def test_add_symbol_ninemlruntimeerror(self):
        """
        line #: 102
        message: Duplicate Symbol '{}' found

        context:
        --------
    def add_symbol(self, symbol):
        if symbol in self.available_symbols:
        """

        nounresolvedsymbolscomponentvalidator = next(instances_of_all_types['NoUnresolvedSymbolsComponentValidator'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            nounresolvedsymbolscomponentvalidator.add_symbol,
            symbol=None)

