"""
This file contains the DynamicsValidator class for validating component

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from builtins import object
from nineml.visitors.validators import NoDuplicatedObjectsValidator
from .general import (
    TimeDerivativesAreDeclaredDynamicsValidator,
    StateAssignmentsAreOnStateVariablesDynamicsValidator,
    AliasesAreNotRecursiveDynamicsValidator,
    NoUnresolvedSymbolsDynamicsValidator,
    RegimeGraphDynamicsValidator,
    RegimeOnlyHasOneHandlerPerEventDynamicsValidator,
    CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator,
    DimensionalityDynamicsValidator)
from .names import (
    LocalNameConflictsDynamicsValidator,
    DimensionNameConflictsDynamicsValidator,
    DuplicateRegimeNamesDynamicsValidator,
    RegimeAliasMatchesBaseScopeValidator)
from .ports import (
    EventPortsDynamicsValidator, OutputAnalogPortsDynamicsValidator)
from .types import (
    TypesDynamicsValidator)


class DynamicsValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, component_class,
                                validate_dimensions=True, **kwargs):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesDynamicsValidator(component_class, **kwargs)
        NoDuplicatedObjectsValidator(component_class, **kwargs)
        DuplicateRegimeNamesDynamicsValidator(component_class, **kwargs)
        LocalNameConflictsDynamicsValidator(component_class, **kwargs)
        DimensionNameConflictsDynamicsValidator(component_class, **kwargs)
        RegimeAliasMatchesBaseScopeValidator(component_class, **kwargs)
        EventPortsDynamicsValidator(component_class, **kwargs)
        OutputAnalogPortsDynamicsValidator(component_class, **kwargs)
        TimeDerivativesAreDeclaredDynamicsValidator(component_class, **kwargs)
        StateAssignmentsAreOnStateVariablesDynamicsValidator(component_class,
                                                             **kwargs)
        AliasesAreNotRecursiveDynamicsValidator(component_class, **kwargs)
        NoUnresolvedSymbolsDynamicsValidator(component_class, **kwargs)
        RegimeGraphDynamicsValidator(component_class, **kwargs)
        RegimeOnlyHasOneHandlerPerEventDynamicsValidator(component_class,
                                                         **kwargs)
        CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator(component_class,
                                                               **kwargs)
        if validate_dimensions:
            DimensionalityDynamicsValidator(component_class, **kwargs)
