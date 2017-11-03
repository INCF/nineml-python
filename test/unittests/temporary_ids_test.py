import unittest
import numpy as np
from nineml.visitors.base import BaseVisitorWithContext
from nineml.abstraction.dynamics import Dynamics
from nineml.user.multi import MultiDynamics
from nineml.utils.comprehensive_example import instances_of_all_types
from nineml.exceptions import NineMLUsageError


class IDsVisitor(BaseVisitorWithContext):

    def __init__(self, as_class, print_all=False):
        BaseVisitorWithContext.__init__(self)
        self.as_class = as_class
        self.print_all = print_all

    def find(self, element):
        self.ids = []
        self.temp_mem_address = set()
        self.visit(element)
        return self.ids, self.temp_mem_address

    def default_action(self, obj, **kwargs):  # @UnusedVariable
        if obj.id in self.ids:
            raise NineMLUsageError(
                "ID of {} {} ({}) already seen [{}]".format(
                    type(obj).__name__, obj, obj.id, self.context_str()))
        if self.print_all:
            print('{}: {}, {} [{}]'.format(obj.id, type(obj).__name__, obj,
                                           self.context_str()))
        self.ids.append(obj.id)
        if obj.temporary:
            self.temp_mem_address.add(id(obj))

    def context_str(self):
        return '>'.join('{}({})'.format(c.parent_cls.__name__, c.parent.key)
                        for c in self.contexts)

    def action_dimension(self, dim, **kwargs):
        pass

    def action_unit(self, unit, **kwargs):
        pass


class TestTemporaryIDs(unittest.TestCase):

    def test_multi_dyn_ids(self):
        visitor = IDsVisitor(Dynamics, print_all=False)
        for multi_dyn in instances_of_all_types[
                MultiDynamics.nineml_type].values():
            first_ids, first_mem_addresses = visitor.find(multi_dyn)
            # Create an array to take up memory slots and make it unlikely that
            # two temporary objects will be in the same place in memory
            dummy_array = np.empty(100000)
            second_ids, second_mem_addresses = visitor.find(multi_dyn)
            self.assertEqual(first_ids, second_ids,
                             "IDs of objects changed between first and second "
                             "visit. There probably is something wrong with "
                             "the 'id' property of a temporary object (e.g. "
                             "it is not marked as temporary")
            self.assertNotEqual(first_mem_addresses, second_mem_addresses)
