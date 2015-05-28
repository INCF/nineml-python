"""
This file contains the DynamicsValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .general import (
    TimeDerivativesAreDeclaredDynamicsValidator,
    StateAssignmentsAreOnStateVariablesDynamicsValidator,
    AliasesAreNotRecursiveDynamicsValidator,
    NoUnresolvedSymbolsDynamicsValidator,
    RegimeGraphDynamicsValidator, NoDuplicatedObjectsDynamicsValidator,
    RegimeOnlyHasOneHandlerPerEventDynamicsValidator,
    CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator,
    DimensionalityDynamicsValidator)
from .namingconflicts import (
    LocalNameConflictsDynamicsValidator,
    DimensionNameConflictsDynamicsValidator,
    DuplicateRegimeNamesDynamicsValidator)
from .ports import (
    EventPortsDynamicsValidator, OutputAnalogPortsDynamicsValidator,
    PortConnectionsDynamicsValidator)
from .types import (
    TypesDynamicsValidator)


class DynamicsValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, component_class):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesDynamicsValidator(component_class)
        NoDuplicatedObjectsDynamicsValidator(component_class)
        DuplicateRegimeNamesDynamicsValidator(component_class)
        LocalNameConflictsDynamicsValidator(component_class)
        DimensionNameConflictsDynamicsValidator(component_class)
        EventPortsDynamicsValidator(component_class)
        OutputAnalogPortsDynamicsValidator(component_class)
        TimeDerivativesAreDeclaredDynamicsValidator(component_class)
        StateAssignmentsAreOnStateVariablesDynamicsValidator(component_class)
        AliasesAreNotRecursiveDynamicsValidator(component_class)
        NoUnresolvedSymbolsDynamicsValidator(component_class)
        PortConnectionsDynamicsValidator(component_class)
        RegimeGraphDynamicsValidator(component_class)
        RegimeOnlyHasOneHandlerPerEventDynamicsValidator(component_class)
        CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator(component_class)
        DimensionalityDynamicsValidator(component_class)
