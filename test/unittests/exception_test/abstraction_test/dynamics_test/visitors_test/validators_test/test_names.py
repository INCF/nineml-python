import unittest
from nineml.abstraction.dynamics.visitors.validators.names import (RegimeAliasMatchesBaseScopeValidator)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestRegimeAliasMatchesBaseScopeValidatorExceptions(unittest.TestCase):

    def test_action_alias_ninemlruntimeerror(self):
        """
        line #: 81
        message: Alias '{}' in regime scope does not match any in the base scope of the Dynamics class '{}'

        context:
        --------
    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias.name not in self.component_class.alias_names:
        """

        regimealiasmatchesbasescopevalidator = instances_of_all_types['RegimeAliasMatchesBaseScopeValidator']
        self.assertRaises(
            NineMLRuntimeError,
            regimealiasmatchesbasescopevalidator.action_alias,
            alias=None)

