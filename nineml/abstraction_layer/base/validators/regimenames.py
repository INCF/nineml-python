"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from base import PerNamespaceValidator
from nineml.utility import assert_no_duplicates


class DuplicateRegimeNamesValidator(PerNamespaceValidator):

    def __init__(self, component):
        PerNamespaceValidator.__init__(
            self, require_explicit_overrides=False)
        self.visit(component)

    def action_componentclass(self, componentclass, namespace):  # @UnusedVariable @IgnorePep8
        regime_names = [r.name for r in componentclass.regimes]
        assert_no_duplicates(regime_names)
