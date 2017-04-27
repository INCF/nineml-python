import re
import os.path
from lxml import etree
from lxml.builder import ElementMaker
from urllib import urlopen
import contextlib
from nineml.document import Document
from nineml.exceptions import NineMLXMLError
from .base import BaseSerializer, BaseUnserializer, NINEML_NS

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'(\{.*\})(.*)')
nineml_version_re = re.compile(r'{}/([\d\.]+)/?'.format(NINEML_NS))


def extract_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(1)


def strip_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(2)


def value_str(value):
    # Ensure all decimal places are preserved for floats
    return repr(value) if isinstance(value, float) else str(value)


class Serializer(BaseSerializer):
    "Serializer class for the XML format"

    def __init__(self, document, version):
        super(Serializer, self).__init__(document, version)
        self._doc_root = self.E()(document.nineml_type)

    def create_elem(self, name, parent=None, namespace=None,
                    **options):  # @UnusedVariable
        elem = self.E(namespace)(name)
        if parent is not None:
            parent.append(elem)
        return elem

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem.attrib[name] = value_str(value)

    def set_body(self, serial_elem, value, sole, **options):  # @UnusedVariable
        serial_elem.text = value_str(value)

    def root_elem(self):
        return self._doc_root

    def E(self, namespace=None):
        if namespace is None:
            namespace = self.nineml_namespace
        return ElementMaker(namespace=namespace,
                            nsmap={None: self.nineml_namespace})


class Unserializer(BaseUnserializer):
    "Unserializer class for the XML format"

    def __init__(self, xml_doc, relative_to=None):
        if isinstance(xml_doc, basestring):
            xml_doc, self._url = self.read_xml(xml_doc,
                                               relative_to=relative_to)
        else:
            self._url = None
        self._xml_root = xml_doc.getroot()
        self._nineml_root = self.get_single_child(self._xml_root)
        namespace = extract_xmlns(self._nineml_root)
        version = nineml_version_re.match(namespace).group(1)
        super(Serializer, self).__init__(Document(), version)

    def get_children(self, serial_elem, **options):  # @UnusedVariable
        return ((strip_xmlns(e.tag), extract_xmlns(e.tag), e)
                for e in serial_elem.getchildren())

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        return serial_elem.attrib[name]

    def get_body(self, serial_elem, sole, **options):  # @UnusedVariable
        body = serial_elem.text
        if body is not None and not body.strip():
            body = None
        return body

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem.attrib.keys()

    def root_elem(self):
        return self._nineml_root

    @classmethod
    def read_xml(cls, url, relative_to):
        if url.startswith('.') and relative_to:
            url = os.path.abspath(os.path.join(relative_to, url))
        try:
            if not isinstance(url, file):
                try:
                    with contextlib.closing(urlopen(url)) as f:
                        xml = etree.parse(f)
                except IOError, e:
                    raise NineMLXMLError("Could not read 9ML URL '{}': \n{}"
                                         .format(url, e))
            else:
                xml = etree.parse(url)
        except etree.LxmlError, e:
            raise NineMLXMLError("Could not parse XML of 9ML file '{}': \n {}"
                                 .format(url, e))
        return xml, url
