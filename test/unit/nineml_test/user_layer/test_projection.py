import os.path
import unittest
from nineml import read, load


class TestProjection(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                             '..', '..', 'examples', 'xml', 'projections',
                             'simple.xml')

    def test_xml_540degree_roundtrip(self):
        context1 = read(self.test_file)
        xml = context1.to_xml()
        context2 = load(xml, read_from=self.test_file)
        for k in context1:
            o1 = context1[k]
            o2 = context2[k]
            if not o1 == o2:
                c1 = o1.response.component_class.dynamics._regimes
                c2 = o2.response.component_class.dynamics._regimes
                for k in c1:
                    if not c1[k] == c2[k]:
                        print c1[k] == c2[k]  # @IgnorePep8
        self.assertEquals(context1, context2)
