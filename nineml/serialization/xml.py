import re
from lxml import etree
from lxml.builder import ElementMaker
from nineml.document import Document
from nineml.exceptions import NineMLSerializationError
from .base import BaseSerializer, BaseUnserializer
from . import NINEML_BASE_NS, DEFAULT_VERSION

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'\{(.*)\}(.*)')
nineml_version_re = re.compile(r'{}([\d\.]+)/?'.format(NINEML_BASE_NS))


def extract_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(1)


def strip_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(2)


def value_str(value):
    # Ensure all decimal places are preserved for floats
    return repr(value) if isinstance(value, float) else str(value)


class Serializer(BaseSerializer):
    "Serializer class for the XML format"

    def __init__(self, version=DEFAULT_VERSION, document=None):
        super(Serializer, self).__init__(version=version, document=document)
        self._root_elem = self.E()(Document.nineml_type)

    def create_elem(self, name, parent=None, namespace=None,
                    **options):  # @UnusedVariable
        elem = self.E(namespace)(name)
        if parent is not None:
            parent.append(elem)
        return elem

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem.attrib[name] = value_str(value)

    def set_body(self, serial_elem, value, sole=False, **options):  # @UnusedVariable @IgnorePep8
        serial_elem.text = value_str(value)

    def root_elem(self):
        return self._root_elem

    def E(self, namespace=None):
        if namespace is None:
            namespace = self.nineml_namespace
        return ElementMaker(namespace=namespace,
                            nsmap={None: self.nineml_namespace})

    def write(self, file_, xml=None, pretty_print=True,
              xml_declaration=True, encoding='UTF-8', **kwargs):  # @UnusedVariable  @IgnorePep8
        if xml is None:
            xml = self.root_elem()
        etree.ElementTree(xml).write(file_, encoding=encoding,
                                     pretty_print=pretty_print,
                                     xml_declaration=xml_declaration)


class Unserializer(BaseUnserializer):
    "Unserializer class for the XML format"

    def __init__(self, file=None, document=None, url=None, **kwargs):  # @ReservedAssignment @IgnorePep8
        self._root_elem = self.read(file)
        namespace = extract_xmlns(self.root_elem().tag)
        try:
            version = nineml_version_re.match(namespace).group(1)
        except AttributeError:
            raise NineMLSerializationError(
                "Provided XML document is not in a valid 9ML namespace {}"
                .format(namespace))
        super(Unserializer, self).__init__(version, url, document=document,
                                           **kwargs)
        if strip_xmlns(self.root_elem().tag) != self.node_name(Document):
            raise NineMLSerializationError(
                "Provided XML document is not enclosed within a '{}' "
                "element".format(self.node_name(Document)))

    def get_children(self, serial_elem, **options):  # @UnusedVariable
        try:
            return ((strip_xmlns(e.tag), extract_xmlns(e.tag), e)
                    for e in serial_elem.getchildren()
                    if not isinstance(e, etree._Comment))
        except:
            raise

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        return serial_elem.attrib[name]

    def get_body(self, serial_elem, sole=True, **options):  # @UnusedVariable
        body = serial_elem.text
        if body is not None and not body.strip():
            body = None
        return body

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem.attrib.keys()

    def root_elem(self):
        return self._root_elem

    def read(self, file):  # @ReservedAssignment
        try:
            xml = etree.parse(file)
        except (etree.LxmlError, IOError) as e:
            raise NineMLSerializationError(
                "Could not read URL or file path '{}': \n{}"
                .format(file, e))
        return xml
