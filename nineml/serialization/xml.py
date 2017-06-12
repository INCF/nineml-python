import re
from lxml import etree
from lxml.builder import ElementMaker
from nineml.document import Document
from nineml.exceptions import NineMLSerializationError
from .base import BaseSerializer, BaseUnserializer
from nineml.exceptions import NineMLNameError
from . import NINEML_BASE_NS, DEFAULT_VERSION

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'\{(.*)\}(.*)')
nineml_version_re = re.compile(r'{}([\d\.]+)/?'.format(NINEML_BASE_NS))


def extract_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(1)


def strip_xmlns(tag_name):
    try:
        return xmlns_re.match(tag_name).group(2)
    except:
        raise


def value_str(value):
    # Ensure all decimal places are preserved for floats
    return repr(value) if isinstance(value, float) else str(value)


class Serializer(BaseSerializer):
    "Serializer class for the XML format"

    def __init__(self, version=DEFAULT_VERSION, document=None, **kwargs):  # @UnusedVariable @IgnorePep8
        super(Serializer, self).__init__(version=version, document=document)

    def create_elem(self, name, parent=None, namespace=None,
                    **options):  # @UnusedVariable
        elem = self.E(namespace)(name)
        if parent is not None:
            parent.append(elem)
        return elem

    def create_root(self):
        return self.E()(Document.nineml_type)

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem.attrib[name] = value_str(value)

    def set_body(self, serial_elem, value, sole=False, **options):  # @UnusedVariable @IgnorePep8
        serial_elem.text = value_str(value)

    def E(self, namespace=None):
        if namespace is None:
            namespace = self.nineml_namespace
        nsmap = {None: namespace}
        return ElementMaker(namespace=namespace,
                            nsmap=nsmap)

    def write_to_file(self, file, serial_elem=None, pretty_print=True,  # @ReservedAssignment @IgnorePep8
              xml_declaration=True, encoding='UTF-8', **kwargs):  # @UnusedVariable  @IgnorePep8
        if serial_elem is None:
            serial_elem = self.root
        etree.ElementTree(serial_elem).write(file, encoding=encoding,
                                             pretty_print=pretty_print,
                                             xml_declaration=xml_declaration)


class Unserializer(BaseUnserializer):
    "Unserializer class for the XML format"

    def __init__(self, root, version=None,  # @ReservedAssignment @IgnorePep8
                 url=None, document=None, **kwargs):
        super(Unserializer, self).__init__(
            root, version=version, url=url, document=document, **kwargs)
        if self.root is not None:
            if strip_xmlns(self.root.tag) != self.node_name(Document):
                raise NineMLSerializationError(
                    "Provided XML document is not enclosed within a '{}' "
                    "element".format(self.node_name(Document)))

    def get_children(self, serial_elem, **options):  # @UnusedVariable
        return ((strip_xmlns(e.tag), extract_xmlns(e.tag), e)
                for e in serial_elem.getchildren()
                if not isinstance(e, etree._Comment))

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        try:
            return serial_elem.attrib[name]
        except KeyError:
            raise NineMLNameError(
                "Element {} doesn't contain '{}' attribute"
                .format(serial_elem, name))

    def get_body(self, serial_elem, sole=True, **options):  # @UnusedVariable
        body = serial_elem.text
        if body is not None and not body.strip():
            body = None
        return body

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem.attrib.keys()

    def extract_version(self):
        namespace = extract_xmlns(self.root.tag)
        try:
            version = nineml_version_re.match(namespace).group(1)
        except AttributeError:
            raise NineMLSerializationError(
                "Provided XML document is not in a valid 9ML namespace {}"
                .format(namespace))
        return version

    def parse_file(self, file):  # @ReservedAssignment
        try:
            xml = etree.parse(file)
        except (etree.LxmlError, IOError) as e:
            raise NineMLSerializationError(
                "Could not read URL or file path '{}': \n{}"
                .format(file, e))
        return xml.getroot()

    def parse_string(self, string):
        try:
            return etree.fromstring(string)
        except etree.LxmlError as e:
            raise NineMLSerializationError(
                "Could not parse XML string '{}': \n{}".format(file, e))

    def parse_elem(self, elem):
        if not isinstance(elem, etree._Element):
            raise NineMLSerializationError(
                "{} is not a valid XML element".format(elem))
        return elem
