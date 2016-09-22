import unittest
from nineml.xml import (from_child_xml, from_child_xml, from_xml_with_exception_handling, from_xml_with_exception_handling)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLXMLBlockError, NineMLXMLAttributeError)


class TestExceptions(unittest.TestCase):

    def test_from_child_xml_ninemlxmlattributeerror(self):
        """
        line #: 74
        message: {} in '{}' has '{}' attributes when {} are expected

        context:
        --------
def from_child_xml(element, child_classes, document, multiple=False,
                   allow_reference=False, allow_none=False, within=None,
                   unprocessed=None, multiple_within=False,
                   allowed_attrib=[], **kwargs):
    \"\"\"
    Loads a child element from the element, matching the tag name to the
    appropriate class and calling its 'from_xml' method
    \"\"\"
    # Ensure child_classes is an iterable
    if isinstance(child_classes, type):
        child_classes = (child_classes,)
    assert child_classes, "No child classes supplied"
    # Get the namespace of the element (i.e. NineML version)
    xmlns = extract_xmlns(element.tag)
    # Get the parent element of the child elements to parse. For example the
    # in Projection elements where pre and post synaptic population references
    # are enclosed within 'Pre' or 'Post' tags respectively
    if within:
        within_elems = element.findall(xmlns + within)
        if len(within_elems) == 1:
            parent = within_elems[0]
            if any(a not in allowed_attrib for a in parent.attrib):
        """

        self.assertRaises(
            NineMLXMLAttributeError,
            from_child_xml,
            element=None,
            child_classes=None,
            document=None,
            multiple=False,
            allow_reference=False,
            allow_none=False,
            within=None,
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_from_child_xml_ninemlxmlblockerror(self):
        """
        line #: 82
        message: {} in '{}' is only expected to contain a single child block, found {}

        context:
        --------
def from_child_xml(element, child_classes, document, multiple=False,
                   allow_reference=False, allow_none=False, within=None,
                   unprocessed=None, multiple_within=False,
                   allowed_attrib=[], **kwargs):
    \"\"\"
    Loads a child element from the element, matching the tag name to the
    appropriate class and calling its 'from_xml' method
    \"\"\"
    # Ensure child_classes is an iterable
    if isinstance(child_classes, type):
        child_classes = (child_classes,)
    assert child_classes, "No child classes supplied"
    # Get the namespace of the element (i.e. NineML version)
    xmlns = extract_xmlns(element.tag)
    # Get the parent element of the child elements to parse. For example the
    # in Projection elements where pre and post synaptic population references
    # are enclosed within 'Pre' or 'Post' tags respectively
    if within:
        within_elems = element.findall(xmlns + within)
        if len(within_elems) == 1:
            parent = within_elems[0]
            if any(a not in allowed_attrib for a in parent.attrib):
                raise NineMLXMLAttributeError(
                    "{} in '{}' has '{}' attributes when {} are expected"
                    .format(identify_element(parent), document.url,
                            "', '".join(parent.attrib.iterkeys()),
                            allowed_attrib))
            if not multiple_within and len([
                    c for c in parent.getchildren()
                    if c.tag != xmlns + 'Annotations']) > 1:
        """

        self.assertRaises(
            NineMLXMLBlockError,
            from_child_xml,
            element=None,
            child_classes=None,
            document=None,
            multiple=False,
            allow_reference=False,
            allow_none=False,
            within=None,
            unprocessed=None,
            multiple_within=False,
            allowed_attrib=[])

    def test_from_xml_with_exception_handling_ninemlxmlblockerror(self):
        """
        line #: 267
        message: Found unrecognised block{s} '{remaining}' within {elem_name} in '{url}'

        context:
        --------
def unprocessed_xml(from_xml):
    def from_xml_with_exception_handling(cls, element, *args, **kwargs):  # @UnusedVariable @IgnorePep8
        # Get the document object for error messages
        if args:  # if UL classmethod
            document = args[0]
            xmlns = extract_xmlns(element.tag)
            if xmlns == NINEMLv1:
                try:
                    nineml_type = cls.v1_nineml_type
                except AttributeError:
                    nineml_type = cls.nineml_type
            else:
                nineml_type = cls.nineml_type
            # Check the tag of the element matches the class names
            assert element.tag in (xmlns + nineml_type), (
                "Found '{}' element, expected '{}'"
                .format(element.tag, cls.nineml_type))
        else:
            document = cls.document  # if AL visitor method
        # Keep track of which blocks and attributes were processed within the
        # element
        unprocessed = (set(e for e in element.getchildren()
                           if not isinstance(e, etree._Comment)),
                       set(element.attrib.iterkeys()))
        # The decorated method
        obj = from_xml(cls, element, *args, unprocessed=unprocessed,
                       **kwargs)
        # Check to see if there were blocks that were unprocessed in the
        # element
        blocks, attrs = unprocessed
        if blocks:
        """

        self.assertRaises(
            NineMLXMLBlockError,
            from_xml_with_exception_handling,
            element=None)

    def test_from_xml_with_exception_handling_ninemlxmlattributeerror(self):
        """
        line #: 274
        message: Found unrecognised attribute{s} '{remaining}' within {elem_name} in '{url}'

        context:
        --------
def unprocessed_xml(from_xml):
    def from_xml_with_exception_handling(cls, element, *args, **kwargs):  # @UnusedVariable @IgnorePep8
        # Get the document object for error messages
        if args:  # if UL classmethod
            document = args[0]
            xmlns = extract_xmlns(element.tag)
            if xmlns == NINEMLv1:
                try:
                    nineml_type = cls.v1_nineml_type
                except AttributeError:
                    nineml_type = cls.nineml_type
            else:
                nineml_type = cls.nineml_type
            # Check the tag of the element matches the class names
            assert element.tag in (xmlns + nineml_type), (
                "Found '{}' element, expected '{}'"
                .format(element.tag, cls.nineml_type))
        else:
            document = cls.document  # if AL visitor method
        # Keep track of which blocks and attributes were processed within the
        # element
        unprocessed = (set(e for e in element.getchildren()
                           if not isinstance(e, etree._Comment)),
                       set(element.attrib.iterkeys()))
        # The decorated method
        obj = from_xml(cls, element, *args, unprocessed=unprocessed,
                       **kwargs)
        # Check to see if there were blocks that were unprocessed in the
        # element
        blocks, attrs = unprocessed
        if blocks:
            raise NineMLXMLBlockError(
                "Found unrecognised block{s} '{remaining}' within "
                "{elem_name} in '{url}'"
                .format(s=('s' if len(blocks) > 1 else ''),
                        remaining="', '".join(str(b.tag) for b in blocks),
                        elem_name=identify_element(element), url=document.url))
        if attrs:
        """

        self.assertRaises(
            NineMLXMLAttributeError,
            from_xml_with_exception_handling,
            element=None)

