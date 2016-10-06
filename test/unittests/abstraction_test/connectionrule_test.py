import unittest
from nineml.abstraction.connectionrule import (
    all_to_all_connection_rule, one_to_one_connection_rule,
    explicit_connection_rule, probabilistic_connection_rule,
    random_fan_in_connection_rule, random_fan_out_connection_rule)
from nineml.user.connectionrule import (ConnectionRuleProperties, Connectivity)


class Connectivity_test(unittest.TestCase):

    def test_all_to_all(self):
        connectivity = Connectivity(
            ConnectionRuleProperties('all_to_all', all_to_all_connection_rule),
            3, 5)
        connections = sorted(connectivity.connections())
        self.assertEqual(
            connections, [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
                          (0, 1), (1, 1), (1, 2), (1, 3), (1, 4),
                          (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)])

    def test_one_to_one(self):
        connectivity = Connectivity(
            ConnectionRuleProperties('one_to_one', one_to_one_connection_rule),
            4, 4)
        connections = sorted(connectivity.connections())
        self.assertEqual(
            connections, [(0, 0), (1, 1), (2, 2), (3, 3)])

    def test_explicit(self):
        connectivity = Connectivity(
            ConnectionRuleProperties('explicit', explicit_connection_rule,
                                     {'sourceIndices': [0, 0, 1, 3, 5],
                                      'destinationIndices': [2, 4, 2, 4, 5]}),
            6, 6)
        connections = sorted(connectivity.connections())
        self.assertEqual(
            connections, [(0, 2), (0, 4), (1, 2), (3, 4), (5, 5)])

    def test_random_fan_in(self):
        connectivity = Connectivity(
            ConnectionRuleProperties(
                'random_fan_in', random_fan_in_connection_rule, {'number': 5}),
            10, 10)
        connections = sorted(connectivity.connections())

    def test_random_fan_out(self):
        connectivity = Connectivity(
            ConnectionRuleProperties(
                'random_fan_out', random_fan_out_connection_rule,
                {'number': 5}), 10, 10)
        connections = sorted(connectivity.connections())

    def test_probabilistic(self):
        connectivity = Connectivity(
            ConnectionRuleProperties(
                'probabilistic', probabilistic_connection_rule,
                {'probability': 0.5}), 10, 10)
        connections = sorted(connectivity.connections())
