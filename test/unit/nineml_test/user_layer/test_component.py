import os.path
import unittest
from nineml import read
from nineml.user_layer import Component
from nineml.exceptions import NineMLUnitMismatchError

examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                            '..', '..', 'examples', 'xml', 'neurons')


class TestComponent(unittest.TestCase):

    def test_load(self):
        context = read(os.path.join(examples_dir, 'HodgkinHuxley.xml'))
        self.assertEquals(type(context['HodgkinHuxley']), Component)

    def test_prototype(self):
        context = read(os.path.join(examples_dir, 'HodgkinHuxleyModified.xml'))
        self.assertEquals(type(context['HodgkinHuxleyModified']), Component)

    def test_mismatch_dimension(self):
        context = read(os.path.join(examples_dir, 'HodgkinHuxleyBadUnits.xml'))
        with self.assertRaises(NineMLUnitMismatchError):
            context['HodgkinHuxleyBadUnits']
