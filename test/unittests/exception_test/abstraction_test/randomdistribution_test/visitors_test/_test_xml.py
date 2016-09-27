import unittest
from nineml.abstraction.randomdistribution.visitors.xml import (RandomDistributionXMLLoader)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLXMLBlockError)


class TestRandomDistributionXMLLoaderExceptions(unittest.TestCase):

    def test_load_randomdistributionclass_ninemlxmlblockerror(self):
        """
        line #: 37
        message: Not expecting {} blocks within 'RandomDistribution' block

        context:
        --------
    def load_randomdistributionclass(self, element, **kwargs):
        xmlns = extract_xmlns(element.tag)
        if xmlns == NINEMLv1:
            lib_elem = expect_single(element.findall(NINEMLv1 +
                                                     'RandomDistribution'))
            if lib_elem.getchildren():
        """

        randomdistributionxmlloader = next(instances_of_all_types['RandomDistributionXMLLoader'].itervalues())
        self.assertRaises(
            NineMLXMLBlockError,
            randomdistributionxmlloader.load_randomdistributionclass,
            element=None)

