import re
from future.utils import native_str_to_bytes, bytes_to_native_str
from lxml import etree
from lxml.builder import ElementMaker
from nineml.document import Document
from nineml.exceptions import (
    NineMLSerializationError, NineMLMissingSerializationError)
from nineml.serialization.base import BaseSerializer, BaseUnserializer
from nineml.exceptions import NineMLNameError
from . import DEFAULT_VERSION

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'\{(.*)\}(.*)')


def extract_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(1)


def strip_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(2)


def value_str(value):
    # Ensure all decimal places are preserved for floats
    return repr(value) if isinstance(value, float) else str(value)


class XMLSerializer(BaseSerializer):
    "Serializer class for the XML format"

    supports_bodies = True

    def __init__(self, version=DEFAULT_VERSION, document=None, **kwargs):  # @UnusedVariable @IgnorePep8
        super(XMLSerializer, self).__init__(version=version, document=document,
                                            **kwargs)

    def create_elem(self, name, parent, namespace=None, **options):  # @UnusedVariable @IgnorePep8
        elem = self.E(namespace)(name)
        parent.append(elem)
        return elem

    def create_root(self):
        return self.E()(Document.nineml_type)

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem.attrib[name] = value_str(value)

    def set_body(self, serial_elem, value, **options):  # @UnusedVariable @IgnorePep8
        serial_elem.text = value_str(value)

    def E(self, namespace=None):
        if namespace is None:
            namespace = self.nineml_namespace
        nsmap = {None: namespace}
        return ElementMaker(namespace=namespace,
                            nsmap=nsmap)

    def to_file(self, serial_elem, file, pretty_print=True,  # @ReservedAssignment @IgnorePep8
                xml_declaration=True, encoding='UTF-8', **kwargs):  # @UnusedVariable  @IgnorePep8
        etree.ElementTree(serial_elem).write(file, encoding=encoding,
                                             pretty_print=pretty_print,
                                             xml_declaration=xml_declaration)

    def to_str(self, serial_elem, pretty_print=False,  # @ReservedAssignment @IgnorePep8
               xml_declaration=False, encoding='UTF-8', **kwargs):  # @UnusedVariable  @IgnorePep8
        return bytes_to_native_str(
            etree.tostring(serial_elem, encoding=encoding,
                           pretty_print=pretty_print,
                           xml_declaration=xml_declaration))

    def to_elem(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem


class XMLUnserializer(BaseUnserializer):
    "Unserializer class for the XML format"

    supports_bodies = True

    def __init__(self, root, version=None,  # @ReservedAssignment @IgnorePep8
                 url=None, document=None, **kwargs):
        super(XMLUnserializer, self).__init__(
            root, version=version, url=url, document=document, **kwargs)
        if self.root is not None:
            if strip_xmlns(self.root.tag) != self.node_name(Document):
                raise NineMLSerializationError(
                    "Provided XML document is not enclosed within a '{}' "
                    "element".format(self.node_name(Document)))

    def get_child(self, parent, nineml_type, **options):
        children = list(self.get_children(parent, nineml_type, **options))
        if not children:
            raise NineMLMissingSerializationError(
                "Expected {} in {}"
                .format(nineml_type, parent))
        elif len(children) > 1:
            raise NineMLSerializationError(
                "Expected 1 {} in {} but found {}"
                .format(nineml_type, parent, len(children)))
        return children[0]

    def get_children(self, parent, nineml_type, **options):  # @UnusedVariable @IgnorePep8
        return (e for n, e in self.get_all_children(parent, **options)
                if n == nineml_type)

    def get_all_children(self, parent, **options):  # @UnusedVariable
        return ((strip_xmlns(e.tag), e) for e in parent.getchildren()
                if not isinstance(e, etree._Comment))

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        try:
            return serial_elem.attrib[name]
        except KeyError:
            raise NineMLNameError(
                "Element {} doesn't contain '{}' attribute"
                .format(serial_elem, name))

    def get_body(self, serial_elem, **options):  # @UnusedVariable
        body = serial_elem.text
        if body is not None and not body.strip():
            body = None
        return body

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        return list(serial_elem.attrib.keys())

    def get_namespace(self, serial_elem, **options):  # @UnusedVariable
        return extract_xmlns(serial_elem.tag)

    def from_file(self, file):  # @ReservedAssignment
        try:
            xml = etree.parse(file)
        except (etree.LxmlError, IOError) as e:
            try:
                name = file.url
            except AttributeError:
                name = file.name
            raise NineMLSerializationError(
                "Could not read URL or file path '{}': \n{}"
                .format(name, e))
        return xml.getroot()

    def from_str(self, string, **options):  # @UnusedVariable
        try:
            return etree.fromstring(native_str_to_bytes(string))
        except etree.LxmlError as e:
            raise NineMLSerializationError(
                "Could not parse XML string '{}': \n{}".format(string, e))

    def from_elem(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem
