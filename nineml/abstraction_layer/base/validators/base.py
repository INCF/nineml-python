"""
This file contains the ComponentValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.utility import Settings

from .types import TypesValidator
from .ports import EventPortsValidator
from .ports import OutputAnalogPortsValidator
from .namingconflicts import (LocalNameConflictsValidator,
                              DimensionNameConflictsValidator)
from .general import TimeDerivativesAreDeclaredValidator
from .general import NoDuplicatedObjectsValidator
from .general import AssignmentsAliasesAndStateVariablesHaveNoUnResolvedSymbolsValidator  # @IgnorePep8
from .general import PortConnectionsValidator
from .general import StateAssignmentsAreOnStateVariablesValidator
from .general import AliasesAreNotRecursiveValidator
from .general import RegimeGraphValidator
from .general import RegimeOnlyHasOneHandlerPerEventValidator
from .general import CheckNoLHSAssignmentsToMathsNamespaceValidator
from ..visitors import ActionVisitor
from equality_checker import ComponentEqualityChecker


class BaseValidator(object):

    def get_warnings(self):
        raise NotImplementedError()


class BaseComponentValidator(object):

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
        TypesValidator(component)
        NoDuplicatedObjectsValidator(component)
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


class PerNamespaceValidator(ActionVisitor, BaseValidator):

    def __init__(self, explicitly_require_action_overrides=True):
        ActionVisitor.__init__(self,
            explicitly_require_action_overrides=explicitly_require_action_overrides)  # @IgnorePep8
        BaseValidator.__init__(self)

    # Over-ride this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):
        namespace = component.get_node_addr()
        ActionVisitor.visit_componentclass(self, component,
                                           namespace=namespace)

