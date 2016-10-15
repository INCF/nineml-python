import unittest
from nineml.abstraction.componentclass.visitors.queriers import (ComponentDimensionResolver)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLNameError)


class TestComponentDimensionResolverExceptions(unittest.TestCase):

    def test__find_element_ninemlnameerror(self):
        """
        line #: 238
        message: '{}' element was not found in component class '{}'

        context:
        --------
    def _find_element(self, sym):
        name = Expression.symbol_to_str(sym)
        element = None
        for scope in reversed(self._scopes):
            try:
                element = scope.element(
                    name, class_map=self.class_to_visit.class_to_member)
            except KeyError:
                pass
        if element is None:
        """

        componentdimensionresolver = next(instances_of_all_types['ComponentDimensionResolver'].itervalues())
        self.assertRaises(
            NineMLNameError,
            componentdimensionresolver._find_element,
            sym=None)

