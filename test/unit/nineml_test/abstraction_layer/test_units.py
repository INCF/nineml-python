import os.path
import unittest
from nineml import read
from nineml.abstraction_layer.units import Unit, Dimension


class TestUnitsDimensions(unittest.TestCase):

    def test_dimension(self):
        context = read(os.path.join(os.path.dirname(__file__), '..', '..',
                                    '..', '..', '..', '..', 'examples', 'xml',
                                    'units.xml'))
        for name in ('voltage', 'conductance', 'conductanceDensity',
                     'per_voltage', 'charge', 'volume', 'permeability',
                     'idealGasConstantDims'):
            self.assertEquals(type(context[name]), Dimension)

    def test_units(self):
        context = read(os.path.join(os.path.dirname(__file__), '..', '..',
                                    '..', '..', '..', '..', 'examples', 'xml',
                                    'units.xml'))
        for name in ('ms', 'hour', 'litre',
                     'uS', 'uF', 'C', 'mol',
                     'cm_per_ms'):
            self.assertEquals(type(context[name]), Unit)
