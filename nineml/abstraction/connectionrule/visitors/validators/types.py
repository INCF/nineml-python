"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ....componentclass.visitors.validators.types import (
    TypesComponentValidator)
from ..base import BaseConnectionRuleVisitor
from ...base import ConnectionRule


class TypesConnectionRuleValidator(TypesComponentValidator,
                                   BaseConnectionRuleVisitor):

    def action_connectionrule(self, connectionrule, **kwargs):  # @UnusedVariable @IgnorePep8
        try:
            assert isinstance(connectionrule, ConnectionRule)
        except:
            raise
