import unittest
from nineml.abstraction.expressions.base import (ExpressionWithLHS, ExpressionWithSimpleLHS)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestExpressionWithLHSExceptions(unittest.TestCase):

    def test_lhs_name_transform_inplace_notimplementederror(self):
        """
        line #: 447
        message: 

        context:
        --------
    def lhs_name_transform_inplace(self, name_map):
        """

        expressionwithlhs = next(instances_of_all_types['ExpressionWithLHS'].itervalues())
        self.assertRaises(
            NotImplementedError,
            expressionwithlhs.lhs_name_transform_inplace,
            name_map=None)

    def test_lhs_atoms_notimplementederror(self):
        """
        line #: 451
        message: 

        context:
        --------
    def lhs_atoms(self):
        """

        expressionwithlhs = next(instances_of_all_types['ExpressionWithLHS'].itervalues())
        with self.assertRaises(NotImplementedError):
            print expressionwithlhs.lhs_atoms


class TestExpressionWithSimpleLHSExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 470
        message: err

        context:
        --------
    def __init__(self, lhs, rhs, assign_to_reserved=False):
        ExpressionWithLHS.__init__(self, rhs)
        if not is_single_symbol(lhs):
            err = 'Expecting a single symbol on the LHS; got: %s' % lhs
        """

        expressionwithsimplelhs = next(instances_of_all_types['ExpressionWithSimpleLHS'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            expressionwithsimplelhs.__init__,
            lhs=None,
            rhs=None,
            assign_to_reserved=False)

    def test___init___ninemlruntimeerror2(self):
        """
        line #: 473
        message: err

        context:
        --------
    def __init__(self, lhs, rhs, assign_to_reserved=False):
        ExpressionWithLHS.__init__(self, rhs)
        if not is_single_symbol(lhs):
            err = 'Expecting a single symbol on the LHS; got: %s' % lhs
            raise NineMLRuntimeError(err)
        if not assign_to_reserved and not is_valid_lhs_target(lhs):
            err = 'Invalid LHS target: %s' % lhs
        """

        expressionwithsimplelhs = next(instances_of_all_types['ExpressionWithSimpleLHS'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            expressionwithsimplelhs.__init__,
            lhs=None,
            rhs=None,
            assign_to_reserved=False)

