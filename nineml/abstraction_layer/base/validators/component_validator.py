"""
This file contains the ComponentValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.utility import Settings

from validators.types import TypesValidator
from validators.ports import EventPortsValidator
from validators.ports import OutputAnalogPortsValidator
from validators.namingconflicts import (LocalNameConflictsValidator,
                                DimensionNameConflictsValidator)
from validators.general import TimeDerivativesAreDeclaredValidator
from validators.general import NoDuplicatedObjectsValidator
# from cv_general import AliasesAndStateVariablesHaveNoUnResolvedSymbolsValidator
from validators.general import AssignmentsAliasesAndStateVariablesHaveNoUnResolvedSymbolsValidator  # @IgnorePep8
from validators.general import PortConnectionsValidator
from validators.general import StateAssignmentsAreOnStateVariablesValidator
from validators.general import AliasesAreNotRecursiveValidator
from validators.general import RegimeGraphValidator
from validators.general import RegimeOnlyHasOneHandlerPerEventValidator
from validators.general import CheckNoLHSAssignmentsToMathsNamespaceValidator
from validators.regimenames import DuplicateRegimeNamesValidator


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

        # Check class structure:
        TypesValidator(component)
        NoDuplicatedObjectsValidator(component)

        DuplicateRegimeNamesValidator(component)
        LocalNameConflictsValidator(component)
        DimensionNameConflictsValidator(component)

        EventPortsValidator(component)
        OutputAnalogPortsValidator(component)
        TimeDerivativesAreDeclaredValidator(component)
        StateAssignmentsAreOnStateVariablesValidator(component)
        AliasesAreNotRecursiveValidator(component)
        AssignmentsAliasesAndStateVariablesHaveNoUnResolvedSymbolsValidator(component)  # @IgnorePep8
        PortConnectionsValidator(component)
        RegimeGraphValidator(component)
        RegimeOnlyHasOneHandlerPerEventValidator(component)
        CheckNoLHSAssignmentsToMathsNamespaceValidator(component)
