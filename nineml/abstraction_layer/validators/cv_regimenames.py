"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from base import ComponentValidatorPerNamespace
from nineml.utility import assert_no_duplicates


class ComponentValidatorDuplicateRegimeNames(ComponentValidatorPerNamespace):

    def __init__(self, component):
        ComponentValidatorPerNamespace.__init__(self, explicitly_require_action_overrides=False)
        self.visit(component)

    def action_componentclass(self, componentclass, namespace):
        regime_names = [r.name for r in componentclass.regimes]
        assert_no_duplicates(regime_names)
