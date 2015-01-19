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
from .general import NoUnresolvedSymbolsValidator  # @IgnorePep8
from .general import PortConnectionsValidator
from .general import StateAssignmentsAreOnStateVariablesValidator
from .general import AliasesAreNotRecursiveValidator
from .general import RegimeGraphValidator
from .general import RegimeOnlyHasOneHandlerPerEventValidator
from .general import CheckNoLHSAssignmentsToMathsNamespaceValidator
from ..visitors import ActionVisitor
from .equality_checker import ComponentEqualityChecker


class BaseValidator(object):

    def get_warnings(self):
        raise NotImplementedError()


class BaseComponentValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, componentclass):
        """ Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        TypesValidator(componentclass)
        NoDuplicatedObjectsValidator(componentclass)
        LocalNameConflictsValidator(componentclass)
        DimensionNameConflictsValidator(componentclass)
        EventPortsValidator(componentclass)
        OutputAnalogPortsValidator(componentclass)
        TimeDerivativesAreDeclaredValidator(componentclass)
        StateAssignmentsAreOnStateVariablesValidator(componentclass)
        AliasesAreNotRecursiveValidator(componentclass)
        NoUnresolvedSymbolsValidator(componentclass)  # @IgnorePep8
        PortConnectionsValidator(componentclass)
        RegimeGraphValidator(componentclass)
        RegimeOnlyHasOneHandlerPerEventValidator(componentclass)
        CheckNoLHSAssignmentsToMathsNamespaceValidator(componentclass)
        ComponentEqualityChecker(componentclass)


class PerNamespaceValidator(ActionVisitor, BaseValidator):

    def __init__(self, explicitly_require_action_overrides=True):
        ActionVisitor.__init__(
            self, explicitly_require_action_overrides=explicitly_require_action_overrides)  # @IgnorePep8
        BaseValidator.__init__(self)

    # Over-ride this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        namespace = component.get_node_addr()
        ActionVisitor.visit_componentclass(self, component,
                                           namespace=namespace)
