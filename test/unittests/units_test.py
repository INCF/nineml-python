import os.path
import unittest
from sympy import sympify
from nineml import read, load, units as un


class TestUnitsDimensions(unittest.TestCase):

    test_file = os.path.join(
        os.path.dirname(__file__), '..', 'xml', 'units.xml')

    def test_xml_540degree_roundtrip(self):
        document1 = read(self.test_file)
        xml = document1.to_xml()
        document2 = load(xml, read_from=self.test_file)
        self.assertEquals(document1, document2)

    def test_sympy(self):
        for dim in (un.temperature, un.capacitance, un.resistance, un.charge,
                    un.voltage, un.specificCapacitance):
            sympy_dim = sympify(dim)
            new_dim = un.Dimension.from_sympy(sympy_dim)
            self.assertEquals(dim, new_dim,
                              "Sympy roundtrip failed for {}".format(dim))
