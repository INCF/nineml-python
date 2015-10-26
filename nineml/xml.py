"""
docstring goes here

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml import etree  # @UnusedImport
from lxml.builder import ElementMaker
from nineml.exceptions import (
    NineMLXMLError, NineMLXMLAttributeError, NineMLXMLBlockError,
    NineMLMissingElementError)
import re
import nineml


nineml_ns = 'http://nineml.net/9ML/2.0'
nineml_v1_ns = 'http://nineml.net/9ML/1.0'
NINEML = '{' + nineml_ns + '}'
NINEML_V1 = '{' + nineml_v1_ns + '}'
MATHML = "{http://www.w3.org/1998/Math/MathML}"
UNCERTML = "{http://www.uncertml.org/2.0}"

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'(\{.*\}).*')

E = ElementMaker(namespace=nineml_ns, nsmap={None: nineml_ns})


def extract_xmlns(tag_name):
    xmlns = xmlns_re.match(tag_name).group(1)
    if xmlns not in (NINEML, NINEML_V1, MATHML, UNCERTML):
        raise NineMLXMLError(
            "Unrecognised namespace '{}'".format(xmlns[1:-1]))
    return xmlns


def from_child_xml(element, child_classes, document, multiple=False,
                   allow_reference=False, allow_none=False, within=None,
                   unprocessed_blocks=set(), **kwargs):
    # Ensure child_classes is an iterable
    if isinstance(child_classes, type):
        child_classes = (child_classes,)
    assert child_classes, "No child classes supplied"
    # Get the namespace of the element (i.e. NineML version)
    xmlns = extract_xmlns(element.tag)
    # Get the name of the element for error messages if present
    try:
        elem_name = element.attrib['name'] + ' ' + element.tag[len(xmlns):]
    except KeyError:
        elem_name = element.tag[len(xmlns):]
    # Get the parent element of the child elements to parse. For example the
    # in Projection elements where pre and post synaptic population references
    # are enclosed within 'Pre' or 'Post' tags respectively
    if within:
        within_elems = element.findall(xmlns + within)
        if len(within_elems) == 1:
            parent = within_elems[0]
        elif not within_elems:
            if allow_none:
                return None
            else:
                raise NineMLXMLBlockError(
                    "Did not find {} block within {} element in '{}'"
                    .format(within, elem_name, document.url))
        else:
            raise NineMLXMLBlockError(
                "Found unexpected multiple {} blocks within {} in '{}'"
                .format(within, elem_name, document.url))
    else:
        parent = element
    # Get the name of the parent and child classes for error messages
    try:
        parent_name = parent.attrib['name'] + ' ' + parent.tag[len(xmlns):]
    except KeyError:
        parent_name = parent.tag[len(xmlns):]
    # Get the list of child class names for error messages
    child_cls_names = "', '".join(c.element_name for c in child_classes)
    # Append all child classes
    children = []
    if allow_reference != 'only':
        for child_cls in child_classes:
            for child_elem in parent.findall(xmlns + child_cls.element_name):
                children.append(child_cls.from_xml(child_elem, document,
                                                   **kwargs))
                unprocessed_blocks.discard(child_elem)
    if allow_reference:
        for ref_elem in parent.findall(
                xmlns + nineml.reference.Reference.element_name):
            ref = nineml.reference.Reference.from_xml(ref_elem, document,
                                                      **kwargs)
            if isinstance(ref.user_object, child_classes):
                children.append(ref.user_object)
                unprocessed_blocks.discard(ref_elem)
    if not children:
        if allow_none:
            result = [] if multiple else None
        else:
            raise NineMLXMLBlockError(
                "Did not find and child blocks with the tag{s} "
                "'{child_cls_names}'in the {parent_name} in '{url}'"
                .format(s=('s' if len(child_classes) else ''),
                        child_cls_names=child_cls_names,
                        parent_name=parent_name, url=document.url))
    elif multiple:
        result = children
    elif len(children) == 1:
        result = children[0]  # Expect single
    else:
        raise NineMLXMLBlockError(
            "Multiple children of types '{}' found within {} in '{}'"
            .format(child_cls_names, parent_name, document.url))
    return result


def get_xml_attr(element, name, document, unprocessed_attrs=set(), **kwargs):  # @UnusedVariable @IgnorePep8
    try:
        attr = element.attrib[name]
    except KeyError, e:
        raise NineMLXMLAttributeError(
            "{} in '{}' is missing the '{}' attribute (found '{}' attributes)"
            .format(identify_element(element), document.url, e,
                    "', '".join(element.attrib.iterkeys())))
    unprocessed_attrs.discard(name)
    return attr


def identify_element(element):
    # Get the namespace of the element (i.e. NineML version)
    xmlns = extract_xmlns(element.tag)
    # Get the name of the element for error messages if present
    try:
        elem_name = element.attrib['name'] + ' ' + element.tag[len(xmlns):]
    except KeyError:
        elem_name = element.tag[len(xmlns):]
    return elem_name


def unprocessed_xml(from_xml):
    def from_xml_with_exception_handling(cls, element, document, **kwargs):  # @UnusedVariable @IgnorePep8
        # Keep track of which blocks were processed within the element
        unprocessed_blocks = set(element.getchildren())
        unprocessed_attrs = set(element.attrb.iterkeys())
        return from_xml(cls, element, document, unprocessed=unprocessed_blocks,
                        unprocessed_attrs, **kwargs)
        # If there were blocks that were unprocessed in the element
        if unprocessed_blocks:
            raise NineMLXMLBlockError(
                "The following unrecognised block{s} '{remaining}' within "
                "{elem_name} in '{url}'"
                .format(s=('s' if len(unprocessed_blocks) > 1 else ''),
                        remaining="', '".join(b.tag
                                              for b in unprocessed_blocks),
                        elem_name=identify_element(element), url=document.url))
        if unprocessed_attrs:
            raise NineMLXMLAttributeError(
                "The following unrecognised attributes{s} '{remaining}' within"
                " {elem_name} in '{url}'"
                .format(s=('s' if len(unprocessed_attrs) > 1 else ''),
                        remaining="', '".join(unprocessed_attrs),
                        elem_name=identify_element(element), url=document.url))
    return from_xml_with_exception_handling
