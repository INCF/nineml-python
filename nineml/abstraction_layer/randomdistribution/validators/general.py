"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.validators import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    NoDuplicatedObjectsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator)
from . import BaseRandomDistributionValidator


class AliasesAreNotRecursiveRandomDistributionValidator(
        AliasesAreNotRecursiveComponentValidator,
        BaseRandomDistributionValidator):

    """Check that aliases are not self-referential"""

    pass


class NoUnresolvedSymbolsRandomDistributionValidator(
        NoUnresolvedSymbolsComponentValidator,
        BaseRandomDistributionValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """
    pass


class NoDuplicatedObjectsRandomDistributionValidator(
        NoDuplicatedObjectsComponentValidator,
        BaseRandomDistributionValidator):

    def action_randomdistributionblock(self, randomdistributionblock, **kwargs):  # @UnusedVariable
        self.all_objects.append(randomdistributionblock)


class CheckNoLHSAssignmentsToMathsNamespaceRandomDistributionValidator(
        CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
        BaseRandomDistributionValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """
    pass
