"""
docstring goes here

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml import etree  # @UnusedImport
from lxml.builder import ElementMaker
from nineml.exceptions import (
    NineMLXMLError, NineMLXMLAttributeError, NineMLXMLBlockError)
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
                   unprocessed=None, **kwargs):
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
            if parent.attrib:
                raise NineMLXMLAttributeError(
                    "{} in '{}' has '{}' attributes when none are expected"
                    .format(identify_element(parent), document.url,
                            "', '".join(parent.attrib.iterkeys())))
            if unprocessed:
                unprocessed[0].discard(parent)
        elif not within_elems:
            if allow_none:
                return None
            else:
                raise NineMLXMLBlockError(
                    "Did not find {} block within {} element in '{}'"
                    .format(within, identify_element(element), document.url))
        else:
            raise NineMLXMLBlockError(
                "Found unexpected multiple {} blocks within {} in '{}'"
                .format(within, identify_element(element), document.url))
    else:
        parent = element
    # Get the list of child class names for error messages
    child_cls_names = "', '".join(c.element_name for c in child_classes)
    # Append all child classes
    children = []
    if allow_reference != 'only':
        for child_cls in child_classes:
            for child_elem in parent.findall(xmlns + child_cls.element_name):
                children.append(child_cls.from_xml(child_elem, document,
                                                   **kwargs))
                if unprocessed and not within:
                    unprocessed[0].discard(child_elem)
    if allow_reference:
        for ref_elem in parent.findall(
                xmlns + nineml.reference.Reference.element_name):
            ref = nineml.reference.Reference.from_xml(ref_elem, document,
                                                      **kwargs)
            if isinstance(ref.user_object, child_classes):
                children.append(ref.user_object)
                if unprocessed and not within:
                    unprocessed[0].discard(ref_elem)
    if not children:
        if allow_none:
            result = [] if multiple else None
        else:
            raise NineMLXMLBlockError(
                "Did not find and child blocks with the tag{s} "
                "'{child_cls_names}'in the {parent_name} in '{url}'"
                .format(s=('s' if len(child_classes) else ''),
                        child_cls_names=child_cls_names,
                        parent_name=identify_element(parent),
                        url=document.url))
    elif multiple:
        result = children
    elif len(children) == 1:
        result = children[0]  # Expect single
    else:
        raise NineMLXMLBlockError(
            "Multiple children of types '{}' found within {} in '{}'"
            .format(child_cls_names, identify_element(parent), document.url))
    return result


def get_xml_attr(element, name, document, unprocessed=None, in_block=False,
                 dtype=str, **kwargs):  # @UnusedVariable @IgnorePep8
    xmlns = extract_xmlns(element.tag)
    if in_block:
        found = element.findall(xmlns + name)
        if len(found) == 1:
            attr_str = found[0].text
            if unprocessed:
                unprocessed[0].discard(found[0])
        elif not found:
            raise NineMLXMLBlockError(
                "Did not find and child blocks with the tag '{}' within {} in "
                "'{url}'".format(name, identify_element(element),
                                 url=document.url))
        else:
            raise NineMLXMLBlockError(
                "Found multiple child blocks with the tag '{}' within {} in "
                "'{url}'".format(name, identify_element(element),
                                 url=document.url))
    else:
        try:
            attr_str = element.attrib[name]
            if unprocessed:
                unprocessed[1].discard(name)
        except KeyError, e:
            try:
                return kwargs['default']
            except KeyError:
                raise NineMLXMLAttributeError(
                    "{} in '{}' is missing the '{}' attribute (found '{}' "
                    "attributes)".format(
                        identify_element(element), document.url, e,
                        "', '".join(element.attrib.iterkeys())))
    try:
        attr = dtype(attr_str)
    except ValueError:
        raise NineMLXMLAttributeError(
            "'{}' attribute of {} in '{}' cannot be converted to {} type"
            .format(name, identify_element(element), document.url, dtype))
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
        # Keep track of which blocks and attributes were processed within the
        # element
        unprocessed = (set(element.getchildren()),
                       set(element.attrib.iterkeys()))
        try:
            obj = from_xml(cls, element, document, unprocessed=unprocessed,
                           **kwargs)
        except TypeError:
            raise
        blocks, attrs = unprocessed
        # If there were blocks that were unprocessed in the element
        if blocks:
            raise NineMLXMLBlockError(
                "Found unrecognised block{s} '{remaining}' within "
                "{elem_name} in '{url}'"
                .format(s=('s' if len(blocks) > 1 else ''),
                        remaining="', '".join(b.tag for b in blocks),
                        elem_name=identify_element(element), url=document.url))
        if attrs:
            raise NineMLXMLAttributeError(
                "Found unrecognised attribute{s} '{remaining}' within "
                "{elem_name} in '{url}'"
                .format(s=('s' if len(attrs) > 1 else ''),
                        remaining="', '".join(attrs),
                        elem_name=identify_element(element), url=document.url))
        return obj
    return from_xml_with_exception_handling
