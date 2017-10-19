import unittest
from nineml.reference import (BaseReference)
from nineml.document import Document
from nineml.exceptions import (NineMLUsageError)


class TestBaseReferenceExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 25
        message: Must supply a document with a non-None URL that is being
        referenced from if definition is a relative URL string, '{}'
        """
        self.assertRaises(
            NineMLUsageError,
            BaseReference,
            name='a_reference',
            document=None,
            url='./a_relative_url.xml')
        self.assertRaises(
            NineMLUsageError,
            BaseReference,
            name='a_reference',
            document=Document(),
            url='./a_relative_url.xml')
# 
#     def test_from_xml_ninemlxmlattributeerror(self):
#         """
#         line #: 86
#         message: References require the element name provided in the XML
#         element text
#         """
#         element = Ev1(Reference.nineml_type)
#         self.assertRaises(
#             NineMLXMLAttributeError,
#             Reference.from_xml,
#             element=element,
#             document=Document())
