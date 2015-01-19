"""
This file contains the ComponentValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.utility import Settings

from .types import ComponentValidatorTypes
from .ports import ComponentValidatorEventPorts
from .ports import ComponentValidatorOutputAnalogPorts
from .namingconflicts import (ComponentValidatorLocalNameConflicts,
                              ComponentValidatorDimensionNameConflicts)
from .general import ComponentValidatorTimeDerivativesAreDeclared
from .general import ComponentValidatorNoDuplicatedObjects
from .general import ComponentValidatorAssignmentsAliasesAndStateVariablesHaveNoUnResolvedSymbols  # @IgnorePep8
from .general import ComponentValidatorPortConnections
from .general import ComponentValidatorStateAssignmentsAreOnStateVariables
from .general import ComponentValidatorAliasesAreNotRecursive
from .general import ComponentValidatorRegimeGraph
from .general import ComponentValidatorRegimeOnlyHasOneHandlerPerEvent
from .general import ComponentValidatorCheckNoLHSAssignmentsToMathsNamespace
from .regimenames import ComponentValidatorDuplicateRegimeNames
from equality_checker import ComponentEqualityChecker


class ComponentValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_component(cls, component):
        """ Tests a componentclass against a variety of tests, to verify its
        internal structure
        """
        if not Settings.enable_component_validation:
            import os
            assert os.getlogin() == 'hull', \
                   """Checking only mike turns off component-validation :) """
            print "**** WARNING WARNIGN COMPONENT VALIDATION TURNRED OFF ****"
            return
        ComponentValidatorTypes(component)
        ComponentValidatorNoDuplicatedObjects(component)
        ComponentValidatorDuplicateRegimeNames(component)
        ComponentValidatorLocalNameConflicts(component)
        ComponentValidatorDimensionNameConflicts(component)
        ComponentValidatorEventPorts(component)
        ComponentValidatorOutputAnalogPorts(component)
        ComponentValidatorTimeDerivativesAreDeclared(component)
        ComponentValidatorStateAssignmentsAreOnStateVariables(component)
        ComponentValidatorAliasesAreNotRecursive(component)
        ComponentValidatorAssignmentsAliasesAndStateVariablesHaveNoUnResolvedSymbols(component)  # @IgnorePep8
        ComponentValidatorPortConnections(component)
        ComponentValidatorRegimeGraph(component)
        ComponentValidatorRegimeOnlyHasOneHandlerPerEvent(component)
        ComponentValidatorCheckNoLHSAssignmentsToMathsNamespace(component)
