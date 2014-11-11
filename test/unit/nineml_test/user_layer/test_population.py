import os.path
import unittest
from nineml import read, load


class TestPopulation(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                             '..', '..', 'examples', 'xml', 'populations',
                             'simple.xml')

    def test_xml_540degree_roundtrip(self):
        context1 = read(self.test_file)
        xml = context1.to_xml()
        context2 = load(xml, read_from=self.test_file)
        for k, v in context1.iteritems():
            v2 = context2[k]
            if not v == v2:
                for i1, i2 in zip(v.operation.items, v2.operation.items):
                    if not i1 == i2:
                        c1 = i1.cell.component_class
                        c2 = i2.cell.component_class
                        print c1 == c2
                        if not c1._parameters == c2._parameters:
                            for name in c1.parameter_names:
                                if not c1.parameter(name) == c2.parameter(name):
                                    p1 = c1.parameter(name)
                                    p2 = c2.parameter(name)
                                    print p1 == p2
        self.assertEquals(context1, context2)
