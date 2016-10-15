import unittest
from nineml.abstraction.connectionrule.visitors.xml import (ConnectionRuleXMLLoader)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLXMLBlockError)


class TestConnectionRuleXMLLoaderExceptions(unittest.TestCase):

    def test_load_connectionruleclass_ninemlxmlblockerror(self):
        """
        line #: 36
        message: Not expecting {} blocks within 'ConnectionRule' block

        context:
        --------
    def load_connectionruleclass(self, element, **kwargs):  # @UnusedVariable
        xmlns = extract_xmlns(element.tag)
        if xmlns == NINEMLv1:
            lib_elem = expect_single(element.findall(NINEMLv1 +
                                                     'ConnectionRule'))
            if lib_elem.getchildren():
        """

        connectionrulexmlloader = instances_of_all_types['ConnectionRuleXMLLoader']
        self.assertRaises(
            NineMLXMLBlockError,
            connectionrulexmlloader.load_connectionruleclass,
            element=None)

