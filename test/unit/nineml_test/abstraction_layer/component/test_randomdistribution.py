import os.path
import unittest
from lxml.etree import _Element, ElementTree
from nineml import read
from nineml.abstraction_layer.random import ComponentClass
import tempfile

examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                            '..', '..', '..', 'catalog', 'randomdistributions')


class TestRandomDistribution(unittest.TestCase):

    def test_load(self):
        context = read(os.path.join(examples_dir, 'normal.xml'))
        self.assertEquals(type(context['NormalDistribution']), ComponentClass)

    def test_to_xml(self):
        context = read(os.path.join(examples_dir, 'normal.xml'))
        comp_class = context['NormalDistribution']
        xml = comp_class.to_xml()
        self.assertEquals(_Element, type(xml))
        with tempfile.TemporaryFile() as f:
            ElementTree(xml).write(f, encoding="UTF-8", pretty_print=True,
                                   xml_declaration=True)
