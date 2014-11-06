import os.path
import unittest
from nineml import read
from nineml.user_layer import Population


class TestPopulation(unittest.TestCase):

    def test_load(self):
        context = read(os.path.join(os.path.dirname(__file__), '..', '..',
                                    '..', '..', '..', '..', 'examples', 'xml',
                                    'populations',  'simple.xml'))
        self.assertEquals(type(context['HHPopulation']), Population)
