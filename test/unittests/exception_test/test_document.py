import unittest
import tempfile
from nineml.document import Document
from nineml.utils.comprehensive_example import (
    instances_of_all_types, doc1, conPropB1)
from nineml.exceptions import (NineMLNameError, NineMLUsageError)
# from tempfile import mkdtemp
import os.path
from nineml.abstraction.dynamics import Trigger
import nineml
import nineml.units as un
from nineml.user import (
    DynamicsProperties, ConnectionRuleProperties, Definition)
from nineml.abstraction import Parameter, Dynamics, Regime
from nineml.abstraction.connectionrule import random_fan_in_connection_rule


class TestDocumentExceptions(unittest.TestCase):

#     def setUp(self):
#         self._temp_dir = mkdtemp()
# 
#     def tearDown(self):
#         shutil.rmtree(self._temp_dir)
# 
#     def test_read_xml_ninemlruntimeerror(self):
#         """
#         line #: 582
#         message: Could not read 9ML URL '{}': {}
#         """
# 
#         self.assertRaises(
#             NineMLUsageError,
#             read_xml,
#             url='http://this_is_a_bad_url.html',
#             relative_to='/a_file.xml')
# 
#     def test_read_xml_ninemlruntimeerror2(self):
#         """
#         line #: 587
#         message: Could not parse XML of 9ML file '{}': {}
#         """
#         bad_xml_path = os.path.join(self._temp_dir, 'bad_xml.xml')
#         with open(bad_xml_path, 'w') as f:
#             f.write("this file doesn't contain xml")
#         self.assertRaises(
#             NineMLUsageError,
#             read_xml,
#             url=bad_xml_path,
#             relative_to='/a_file.xml')
# 
#     def test_get_component_class_type_ninemlxmlerror(self):
#         """
#         line #: 607
#         message: No type defining block in ComponentClass
#         """
#         elem = Ev1.ComponentClass(name="a")
#         self.assertRaises(
#             NineMLXMLError,
#             get_component_class_type,
#             elem=elem)

    def test_add_ninemlruntimeerror(self):
        """
        line #: 66
        message: Could not add {} to document '{}' as it is not a 'document
        level NineML object' ('{}')
        """
        self.assertRaises(
            NineMLUsageError,
            doc1.add,
            nineml_obj=Trigger('a > b'))

    def test_add_ninemlnameerror(self):
        """
        line #: 75
        message: Could not add element '{}' as an element with that name
        already exists in the document '{}'
        """
        dynB = instances_of_all_types['Dynamics']['dynA'].clone()
        dynB._name = 'dynB'
        self.assertRaises(
            NineMLNameError,
            doc1.add,
            nineml_obj=dynB)

#     def test_add_ninemlruntimeerror2(self):
#         """
#         line #: 84
#         message: Attempting to add the same object '{}' {} to '{}'
#         document when it is already in '{}'. Please remove it from the original
#         document first
#         """
# 
#         doc1 = instances_of_all_types[Document.nineml_type]['doc1']
#         doc2 = Document()
#         self.assertRaises(
#             NineMLUsageError,
#             doc2.add,
#             element=doc1['dynA'])

    def test_remove_ninemlruntimeerror(self):
        """
        line #: 96
        message: Could not remove {} from document as it is not a document
        level NineML object ('{}')
        """
        self.assertRaises(
            NineMLUsageError,
            doc1.remove,
            nineml_obj=Trigger('a > b'))

    def test_remove_ninemlnameerror(self):
        """
        line #: 103
        message: Could not find '{}' element to remove from document '{}'
        """
        conPropZZ = ConnectionRuleProperties(name='ZZ', definition=conPropB1)
        self.assertRaises(
            NineMLNameError,
            doc1.remove,
            nineml_obj=conPropZZ,
            ignore_missing=False)

    def test___getitem___ninemlnameerror(self):
        """
        line #: 137
        message: '{}' was not found in the NineML document {} (elements in the
        document were '{}').
        """
        self.assertRaises(
            NineMLNameError,
            doc1.__getitem__,
            name='ZZ')
# 
#     def test__load_elem_from_xml_ninemlruntimeerror(self):
#         """
#         line #: 217
#         message: Circular reference detected in '{}(name={})' element.
#         Resolution stack was:
#         """
#         xml = Ev2(Document.nineml_type,
#                   Ev2(DynamicsProperties.nineml_type,
#                       Ev2(Definition.nineml_type, name="B"),
#                       name="A"),
#                   Ev2(DynamicsProperties.nineml_type,
#                       Ev2(Definition.nineml_type, name="A"),
#                       name="B"))
#         document = Uxml(root=xml).unserialize()
#         self.assertRaises(
#             NineMLUsageError,
#             document._load_elem_from_xml,
#             unloaded=super(Document, document).__getitem__('A'))

    def test_standardize_units_ninemlruntimeerror(self):
        """
        line #: 257
        message: Name of unit '{}' conflicts with existing object of differring
        value or type '{}' and '{}'
        """
        a = ConnectionRuleProperties(
            name='A',
            definition=random_fan_in_connection_rule,
            properties={'number': (
                1.0 * un.Unit(dimension=un.dimensionless, power=0,
                              name='U'))})
        b = ConnectionRuleProperties(
            name='B',
            definition=random_fan_in_connection_rule,
            properties={'number': (
                1.0 * un.Unit(dimension=un.dimensionless, power=1,
                              name='U'))})
        self.assertRaises(
            NineMLUsageError,
            Document, a, b)

    def test_standardize_units_ninemlruntimeerror2(self):
        """
        line #: 268
        message: Name of dimension '{}' conflicts with existing object of
        differring value or type '{}' and '{}'
        """
        a = Dynamics(
            name='A',
            parameters=[
                Parameter('P1', dimension=un.Dimension(name='D', t=1))],
            regime=Regime(name='default'),
            aliases=['A1 := P1 * 2'])
        b = Dynamics(
            name='B',
            parameters=[
                Parameter('P1', dimension=un.Dimension(name='D', l=1))],
            regime=Regime(name='default'),
            aliases=['A1 := P1 * 2'])
        self.assertRaises(
            NineMLUsageError,
            Document, a, b)
# 
#     def test_from_xml_ninemlxmlerror(self):
#         """
#         line #: 312
#         message: Unrecognised XML namespace '{}', can be one of '{}'
#         """
#         bad_E = ElementMaker(namespace='http://bad_namespace.net')
#         self.assertRaises(
#             NineMLXMLError,
#             Document.from_xml,
#             element=bad_E.AnElement())
# 
#     def test_from_xml_ninemlxmlerror2(self):
#         """
#         line #: 317
#         message: '{}' document does not have a NineML root ('{}')
#         """
#         self.assertRaises(
#             NineMLXMLError,
#             Document.from_xml,
#             element=Ev2.BadRoot())
# 
#     def test_from_xml_ninemlruntimeerror(self):
#         """
#         line #: 340
#         message: '{}' element does not correspond to a recognised
#         document-level object
#         """
#         self.assertRaises(
#             NineMLUsageError,
#             Document.from_xml,
#             element=Ev2(Trigger.nineml_type, 'a > b'))
# 
#     def test_from_xml_ninemlxmlerror3(self):
#         """
#         line #: 350
#         message: Did not find matching NineML class for '{}' element
#         """
#         self.assertRaises(
#             NineMLXMLError,
#             Document.from_xml,
#             element=Ev2.BadElement())
# 
#     def test_from_xml_notimplementederror(self):
#         """
#         line #: 358
#         message: Cannot load '{}' element (extensions not implemented)
#         """
#         unrecogised_E = ElementMaker(namespace='http://unrecognised.net')
#         element = Ev2(Document.nineml_type,
#                       unrecogised_E.UnrecognisedExtension())
#         self.assertRaises(
#             NotImplementedError,
#             Document.from_xml,
#             element=element)
# 
#     def test_from_xml_ninemlxmlerror5(self):
#         """
#         line #: 369
#         message: Missing 'name' (or 'symbol') attribute from document level
#         object '{}'
#         """
#         elem = Ev2(Document.nineml_type,
#                    Ev2(Dynamics.nineml_type))
#         self.assertRaises(
#             NineMLXMLError,
#             Document.from_xml,
#             element=elem)
# 
#     def test_from_xml_ninemlxmlerror6(self):
#         """
#         line #: 373
#         message: Duplicate identifier '{ob1}:{name}'in NineML file '{url}'
#         """
#         xml = Ev2(Document.nineml_type,
#                   Ev2(Dynamics.nineml_type,
#                       name='A'),
#                   Ev2(Dynamics.nineml_type,
#                       name='A'))
#         self.assertRaises(
#             NineMLXMLError,
#             Document.from_xml,
#             element=xml)

#     def test_url_ninemlruntimeerror(self):
#         """
#         line #: 464
#         message: Cannot reset a documents url to None once it has been
#         set('{}') please duplicate the document instead
#         """
#         doc = Document(
#             Dynamics(
#                 name='A',
#                 parameters=[
#                     Parameter('P1', dimension=un.Dimension(name='D', t=1))],
#                 regime=Regime(name='default'),
#                 aliases=['A1 := P1 * 2']))
#         tmp_dir = tempfile.mkdtemp()
#         url = os.path.join(tmp_dir, 'a_url.xml')
#         doc._url = url
#         with self.assertRaises(NineMLUsageError):
#             doc.url = None

#     def test_url_ninemlruntimeerror2(self):
#         """
#         line #: 472
#         message: Cannot set url of document to '{}' as there is already a
#         document loaded in memory with that url. Please remove all references
#         to it first
#         (see https://docs.python.org/2/c-api/intro.html#objects-types-and-
#         reference-counts)
#         """
#         a = Document(
#             Dynamics(
#                 name='A',
#                 parameters=[
#                     Parameter('P1', dimension=un.Dimension(name='D', t=1))],
#                 regime=Regime(name='default'),
#                 aliases=['A1 := P1 * 2']))
#         b = Document(
#             Dynamics(
#                 name='A',
#                 parameters=[
#                     Parameter('P1', dimension=un.Dimension(name='D', t=1))],
#                 regime=Regime(name='default'),
#                 aliases=['A1 := P1 * 2']))
#         tmp_dir = tempfile.mkdtemp()
#         url = os.path.join(tmp_dir, 'a_url.xml')
#         a._url = url
#         with self.assertRaises(NineMLUsageError):
#             b.url = url

#     def test_url_ninemlruntimeerror3(self):
#         """
#         line #: 488
#         message: {} is not a valid URL
#         """
#         doc = Document(
#             Dynamics(
#                 name='A',
#                 parameters=[
#                     Parameter('P1', dimension=un.Dimension(name='D', t=1))],
#                 regime=Regime(name='default'),
#                 aliases=['A1 := P1 * 2']))
#         with self.assertRaises(NineMLUsageError):
#             doc.url = 1
#         with self.assertRaises(NineMLUsageError):
#             doc.url = '*;l22f23'
#         with self.assertRaises(NineMLUsageError):
#             doc.url = 'a_file.xml'  # Not relative file path
#         with self.assertRaises(NineMLUsageError):
#             doc.url = '.../a_file.xml'  # Not relative file path
