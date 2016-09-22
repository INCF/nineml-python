import unittest
from nineml.user.multi.namespace import (_NamespaceExpression, split_namespace, split_multi_regime_name)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLNameError, NineMLImmutableError)


class TestExceptions(unittest.TestCase):

    def test_split_namespace_ninemlnameerror(self):
        """
        line #: 49
        message: Identifier '{}' does not belong to a sub-namespace

        context:
        --------
def split_namespace(identifier_in_namespace):
    \"\"\"
    Splits an identifer and a namespace that have been concatenated by
    'append_namespace'
    \"\"\"
    parts = double_underscore_re.split(identifier_in_namespace)
    if len(parts) < 2:
        """

        self.assertRaises(
            NineMLNameError,
            split_namespace,
            identifier_in_namespace=None)

    def test_split_multi_regime_name_ninemlnameerror(self):
        """
        line #: 92
        message: '{}' is not a multi-regime name

        context:
        --------
def split_multi_regime_name(name):
    parts = triple_underscore_re.split(name)
    if not parts:
        """

        self.assertRaises(
            NineMLNameError,
            split_multi_regime_name,
            name=None)


class Test_NamespaceExpressionExceptions(unittest.TestCase):

    def test_lhs_name_transform_inplace_ninemlimmutableerror(self):
        """
        line #: 154
        message: Cannot change LHS of expression in global namespace of multi-component element. The multi-component elemnt should either be flattened or the substitution should be done in the sub-component

        context:
        --------
    def lhs_name_transform_inplace(self, name_map):
        """

        _namespaceexpression = next(instances_of_all_types['_NamespaceExpression'].itervalues())
        self.assertRaises(
            NineMLImmutableError,
            _namespaceexpression.lhs_name_transform_inplace,
            name_map=None)

    def test_rhs_ninemlimmutableerror(self):
        """
        line #: 174
        message: Cannot change expression in global namespace of multi-component element. The multi-component elemnt should either be flattened or the substitution should be done in the sub-component

        context:
        --------
    def rhs(self, rhs):
        """

        _namespaceexpression = next(instances_of_all_types['_NamespaceExpression'].itervalues())
        with self.assertRaises(NineMLImmutableError):
            _namespaceexpression.rhs = None

    def test_rhs_name_transform_inplace_ninemlimmutableerror(self):
        """
        line #: 181
        message: Cannot change expression in global namespace of multi-component element. The multi-component elemnt should either be flattened or the substitution should be done in the sub-component

        context:
        --------
    def rhs_name_transform_inplace(self, name_map):
        """

        _namespaceexpression = next(instances_of_all_types['_NamespaceExpression'].itervalues())
        self.assertRaises(
            NineMLImmutableError,
            _namespaceexpression.rhs_name_transform_inplace,
            name_map=None)

    def test_rhs_substituted_ninemlimmutableerror(self):
        """
        line #: 188
        message: Cannot change expression in global namespace of multi-component element. The multi-component elemnt should either be flattened or the substitution should be done in the sub-component

        context:
        --------
    def rhs_substituted(self, name_map):
        """

        _namespaceexpression = next(instances_of_all_types['_NamespaceExpression'].itervalues())
        self.assertRaises(
            NineMLImmutableError,
            _namespaceexpression.rhs_substituted,
            name_map=None)

    def test_subs_ninemlimmutableerror(self):
        """
        line #: 195
        message: Cannot change expression in global namespace of multi-component element. The multi-component elemnt should either be flattened or the substitution should be done in the sub-component

        context:
        --------
    def subs(self, old, new):
        """

        _namespaceexpression = next(instances_of_all_types['_NamespaceExpression'].itervalues())
        self.assertRaises(
            NineMLImmutableError,
            _namespaceexpression.subs,
            old=None,
            new=None)

    def test_rhs_str_substituted_ninemlimmutableerror(self):
        """
        line #: 202
        message: Cannot change expression in global namespace of multi-component element. The multi-component elemnt should either be flattened or the substitution should be done in the sub-component

        context:
        --------
    def rhs_str_substituted(self, name_map={}, funcname_map={}):
        """

        _namespaceexpression = next(instances_of_all_types['_NamespaceExpression'].itervalues())
        self.assertRaises(
            NineMLImmutableError,
            _namespaceexpression.rhs_str_substituted,
            name_map={},
            funcname_map={})

