import unittest
from itertools import chain
from nineml.xml import (
    get_element_maker, from_child_xml, from_child_xml,
    from_child_xml, from_child_xml, from_child_xml, get_xml_attr,
    get_subblock)
from nineml.utils.testing.comprehensive import (doc1, dynPropA)
from nineml.exceptions import (
    NineMLXMLAttributeError, NineMLXMLBlockError, NineMLRuntimeError)
from nineml.user import Projection, Population, Definition, DynamicsProperties
from nineml.xml import Ev2
from nineml.reference import Reference


class TestExceptions(unittest.TestCase):

    def test_get_element_maker_ninemlruntimeerror(self):
        """
        line #: 39
        message: Unrecognised 9ML version {} (1.0
        """
        self.assertRaises(
            NineMLRuntimeError,
            get_element_maker,
            version=-1.0)

    def test_from_child_xml_ninemlxmlattributeerror(self):
        """
        line #: 74
        message: {} in '{}' has '{}' attributes when {} are expected
        """
        elem = Ev2(Projection.nineml_type,
                   Ev2.Pre(Ev2(Reference.nineml_type,
                               name="popA"),
                           bad_attr="bar"))
        self.assertRaises(
            NineMLXMLAttributeError,
            from_child_xml,
            element=elem,
            child_classes=(Population,),
            document=doc1,
            multiple=False,
            allow_reference=True,
            allow_none=False,
            within='Pre',
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_from_child_xml_ninemlxmlblockerror(self):
        """
        line #: 82
        message: {} in '{}' is only expected to contain a single child block,
        found {}
        """
        elem = Ev2(Projection.nineml_type,
                   Ev2.Pre(Ev2(Reference.nineml_type,
                               name="popA"),
                           Ev2(Reference.nineml_type,
                               name="popA")))
        self.assertRaises(
            NineMLXMLBlockError,
            from_child_xml,
            element=elem,
            child_classes=(Population,),
            document=doc1,
            multiple=False,
            allow_reference=True,
            allow_none=False,
            within='Pre',
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_from_child_xml_ninemlxmlblockerror2(self):
        """
        line #: 93
        message: Did not find {} block within {} element in '{}'
        """
        elem = Ev2(Projection.nineml_type)
        self.assertRaises(
            NineMLXMLBlockError,
            from_child_xml,
            element=elem,
            child_classes=(Population,),
            document=doc1,
            multiple=False,
            allow_reference=True,
            allow_none=False,
            within='Pre',
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_from_child_xml_ninemlxmlblockerror3(self):
        """
        line #: 97
        message: Found unexpected multiple {} blocks within {} in '{}'
        """
        elem = Ev2(Projection.nineml_type,
                   Ev2.Pre(Ev2(Reference.nineml_type,
                               name="popA")),
                   Ev2.Pre(Ev2(Reference.nineml_type,
                               name="popB")))
        self.assertRaises(
            NineMLXMLBlockError,
            from_child_xml,
            element=elem,
            child_classes=(Population,),
            document=doc1,
            multiple=False,
            allow_reference=True,
            allow_none=False,
            within='Pre',
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_from_child_xml_ninemlxmlblockerror4(self):
        """
        line #: 133
        message: Did not find any child blocks with the tag{s}
        '{child_cls_names}'in the {parent_name} in '{url}'
        """
        elem = Ev2(DynamicsProperties.nineml_type,
                   Ev2(Definition.nineml_type,
                       name="dynA"),
                   Ev2(Definition.nineml_type,
                       name="dynB"))
        self.assertRaises(
            NineMLXMLBlockError,
            from_child_xml,
            element=elem,
            child_classes=(Definition,),
            document=doc1,
            multiple=False,
            allow_reference=False,
            allow_none=False,
            within=None,
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_from_child_xml_ninemlxmlblockerror5(self):
        """
        line #: 145
        message: Multiple children of types '{}' found within {} in '{}'
        """
        elem = Ev2(DynamicsProperties.nineml_type)
        self.assertRaises(
            NineMLXMLBlockError,
            from_child_xml,
            element=elem,
            child_classes=(Definition,),
            document=doc1,
            multiple=False,
            allow_reference=False,
            allow_none=False,
            within=None,
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_get_xml_attr_ninemlxmlattributeerror(self):
        """
        line #: 172
        message: {} in '{}' is missing the {} attribute (found '{}' attributes)
        """
        elem = Ev2(DynamicsProperties.nineml_type)
        self.assertRaises(
            NineMLXMLAttributeError,
            get_xml_attr,
            element=elem,
            name='name',
            document=doc1)

    def test_get_xml_attr_ninemlxmlattributeerror2(self):
        """
        line #: 183
        message: '{}' attribute of {} in '{}', {}, cannot be converted to {}
        type
        """
        elem = Ev2(DynamicsProperties.nineml_type,
                   name='foo')
        self.assertRaises(
            NineMLXMLAttributeError,
            get_xml_attr,
            element=elem,
            name='name',
            document=doc1,
            dtype=int)

    def test_get_subblock_ninemlxmlblockerror(self):
        """
        line #: 197
        message: Did not find and child blocks with the tag '{}' within {} in
        '{url}'
        """
        elem = Ev2(Population.nineml_type,
                   Ev2('ASubBlock'))
        self.assertRaises(
            NineMLXMLBlockError,
            get_subblock,
            element=elem,
            name='AnotherSubBlock',
            unprocessed=[[]],
            document=doc1)

    def test_get_subblock_ninemlxmlblockerror2(self):
        """
        line #: 202
        message: Found multiple child blocks with the tag '{}' within {} in
        '{url}'
        """
        elem = Ev2(Population.nineml_type,
                   Ev2('ASubBlock'),
                   Ev2('ASubBlock'))
        self.assertRaises(
            NineMLXMLBlockError,
            get_subblock,
            element=elem,
            name='ASubBlock',
            unprocessed=[[]],
            document=doc1)

    def test_from_xml_with_exception_handling_ninemlxmlblockerror(self):
        """
        line #: 267
        message: Found unrecognised block{s} '{remaining}' within {elem_name}
        in '{url}'
        """
        elem = Ev2(DynamicsProperties.nineml_type,
                   dynPropA.to_xml(doc1),
                   Ev2('BadBlock'),
                   *list(chain(
                       (p.to_xml(doc1) for p in dynPropA.properties),
                       (v.to_xml(doc1) for v in dynPropA.initial_values))),
                   name='dynPropA2')
        self.assertRaises(
            NineMLXMLBlockError,
            DynamicsProperties.from_xml,
            element=elem,
            document=doc1)

    def test_from_xml_with_exception_handling_ninemlxmlattributeerror(self):
        """
        line #: 274
        message: Found unrecognised attribute{s} '{remaining}' within
        {elem_name} in '{url}'
        """
        elem = Ev2(DynamicsProperties.nineml_type,
                   dynPropA.to_xml(doc1),
                   *list(chain(
                       (p.to_xml(doc1) for p in dynPropA.properties),
                       (v.to_xml(doc1) for v in dynPropA.initial_values))),
                   name='dynPropA2',
                   bad_attr='bad')
        self.assertRaises(
            NineMLXMLBlockError,
            DynamicsProperties.from_xml,
            element=elem,
            document=doc1)
