import os.path
import unittest
from nineml import read
from nineml.user_layer import Component


class TestComponent(unittest.TestCase):

    def test_load(self):
        context = read(os.path.join(os.path.dirname(__file__), '..', '..',
                                    '..', '..', '..', '..', 'examples', 'xml',
                                    'neurons',  'HodgkinHuxley.xml'))
        self.assertEquals(type(context['HodgkinHuxley']), Component)

    def test_prototype(self):
        context = read(os.path.join(os.path.dirname(__file__), '..', '..',
                                    '..', '..', '..', '..', 'examples', 'xml',
                                    'neurons',  'HodgkinHuxleyModified.xml'))
        self.assertEquals(type(context['HodgkinHuxleyModified']), Component)
