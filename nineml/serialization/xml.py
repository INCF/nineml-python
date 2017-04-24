import re
from lxml.builder import ElementMaker
from .base import BaseSerializer, BaseUnserializer

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'(\{.*\})(.*)')


def extract_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(1)


def strip_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(2)


class Serializer(BaseSerializer):
    "Serializer class for the XML format"

    def create_elem(self, name, parent=None, **options):  # @UnusedVariable
        elem = self.E(name)
        if parent is not None:
            parent.append(elem)
        return elem

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem.attr[name] = str(value)

    def set_body(self, serial_elem, value, **options):  # @UnusedVariable
        serial_elem.text = str(value)

    @property
    def E(self):
        return ElementMaker(namespace=self.namespace,
                            nsmap={None: self.namespace})


class Unserializer(BaseUnserializer):
    "Unserializer class for the XML format"

    def get_children(self, serial_elem, **options):  # @UnusedVariable
        return ((strip_xmlns(e.tag), e) for e in serial_elem.getchildren())

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        return serial_elem.attr[name]

    def get_body(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem.text

    def get_keys(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem.attr.keys() + zip(
            self.get_children(self.serial_elem))[0]
