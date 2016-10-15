"""
Tests for the user module
"""


import unittest
from nineml.user import Property
from nineml import Unit, Dimension
from nineml.document import Document

voltage = Dimension('voltage', m=1, l=2, t=-3, i=-1)
mV = Unit(name='mV', dimension=voltage, power=-3)


class ModelTest(unittest.TestCase):
    pass


class DefinitionTest(unittest.TestCase):
    pass


class BaseComponentTest(unittest.TestCase):
    pass


class SpikingNodeTypeTest(unittest.TestCase):
    pass


class SynapseTypeTest(unittest.TestCase):
    pass


class CurrentSourceTypeTest(unittest.TestCase):
    pass


class StructureTest(unittest.TestCase):
    pass


class ConnectionRuleTest(unittest.TestCase):
    pass


class ConnectionTypeTest(unittest.TestCase):
    pass


class RandomDistributionTest(unittest.TestCase):
    pass


class ParameterTest(unittest.TestCase):

    def test_xml_roundtrip(self):
        p1 = Property("tau_m", 20.0, mV)
        document = Document()
        element = p1.to_xml(document)
        p2 = Property.from_xml(element, document)
        self.assertEqual(p1, p2)


class ParameterSetTest(unittest.TestCase):
    pass


class ValueTest(unittest.TestCase):
    pass


class StringValueTest(unittest.TestCase):
    pass


class GroupTest(unittest.TestCase):
    pass


class PopulationTest(unittest.TestCase):
    pass


class PositionListTest(unittest.TestCase):
    pass


class OperatorTest(unittest.TestCase):
    pass


class SelectionTest(unittest.TestCase):
    pass


class ProjectionTest(unittest.TestCase):
    pass
