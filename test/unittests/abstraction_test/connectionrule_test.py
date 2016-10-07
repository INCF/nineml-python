from __future__ import division
from itertools import groupby
import unittest
import random
from nineml.abstraction.connectionrule import (
    all_to_all_connection_rule, one_to_one_connection_rule,
    explicit_connection_rule, probabilistic_connection_rule,
    random_fan_in_connection_rule, random_fan_out_connection_rule)
from nineml.user.connectionrule import (ConnectionRuleProperties, Connectivity)

# Fix seed to remove stochasticity from probabilistic connectivity
random.seed(12345)


class Connectivity_test(unittest.TestCase):

    def test_all_to_all(self):
        connectivity = Connectivity(
            ConnectionRuleProperties('all_to_all', all_to_all_connection_rule),
            3, 5)
        connections = sorted(connectivity.connections())
        self.assertEqual(
            connections, [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
                          (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
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
        number = 5
        connectivity = Connectivity(
            ConnectionRuleProperties(
                'random_fan_in', random_fan_in_connection_rule,
                {'number': number}), 10, 10)
        connections = sorted(connectivity.connections(),
                             key=lambda c: c[1])
        for dest, conns in groupby(connections, key=lambda c: c[1]):
            num_conns = len(list(conns))
            self.assertEqual(num_conns, number,
                             "Destination index {} has {} connections when {} "
                             "were expected from random fan in rule"
                             .format(dest, num_conns, number))

    def test_random_fan_out(self):
        number = 5
        connectivity = Connectivity(
            ConnectionRuleProperties(
                'random_fan_out', random_fan_out_connection_rule,
                {'number': number}), 10, 10)
        connections = sorted(connectivity.connections(), key=lambda c: c[0])
        for src, conns in groupby(connections, key=lambda c: c[0]):
            num_conns = len(list(conns))
            self.assertEqual(num_conns, number,
                             "Source index {} has {} connections when {} were "
                             "expected from random fan out rule"
                             .format(src, num_conns, number))

    def test_probabilistic(self):
        p = 0.15
        size = 1000
        connectivity = Connectivity(
            ConnectionRuleProperties(
                'probabilistic', probabilistic_connection_rule,
                {'probability': p}), size, size)
        num_conns = len(list(connectivity.connections()))
        self.assertAlmostEqual(num_conns / size ** 2, p, 2)
