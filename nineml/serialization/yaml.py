from __future__ import absolute_import
from future.utils import native_str_to_bytes, bytes_to_native_str, PY3
from .dict import DictSerializer, DictUnserializer
from collections import OrderedDict
from nineml.document import Document
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper  # @UnusedImport
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(iter(data.items()))


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

Dumper.add_representer(OrderedDict, dict_representer)
Loader.add_constructor(_mapping_tag, dict_constructor)


class YAMLSerializer(DictSerializer):
    """
    A Serializer class that serializes to YAML
    """

    def to_file(self, serial_elem, file, **options):
        yaml.dump(self._prepare_dict(serial_elem, **options), stream=file,
                  Dumper=Dumper)

    def to_str(self, serial_elem, **options):
        return yaml.dump(self.to_elem(serial_elem, **options),
                         Dumper=Dumper)

    def _prepare_dict(self, elem_dict, **options):
        elem_dict = self.to_elem(elem_dict, **options)
        if PY3:
            elem_dict = self.convert_to_bytes(elem_dict)
        return elem_dict

    @classmethod
    def convert_to_bytes(cls, elem):
        if isinstance(elem, str):
            elem = native_str_to_bytes(elem)
        elif isinstance(elem, list):
            elem = [cls.convert_to_bytes(e) for e in elem]
        elif isinstance(elem, dict):
            elem = OrderedDict(
                (native_str_to_bytes(n), cls.convert_to_bytes(e))
                for n, e in elem.items())
        return elem

    @classmethod
    def open_file(cls, url):
        return open(url, 'w')


class YAMLUnserializer(DictUnserializer):
    """
    A Unserializer class that unserializes YAML
    """

    def from_file(self, file, **options):
        return self._finalise_dict(yaml.load(file, Loader=Loader), **options)

    def from_str(self, string, **options):
        return self.from_elem(yaml.load(string, Loader=Loader), **options)

    def _finalise_dict(self, elem_dict, nineml_type=None, **options):
        if nineml_type is None:
            nineml_type = Document.nineml_type
        nineml_type = native_str_to_bytes(nineml_type)
        elem_dict = self.from_elem(elem_dict, nineml_type=nineml_type,
                                   **options)
        if PY3:
            elem_dict = self.convert_from_bytes(elem_dict)
        return elem_dict

    @classmethod
    def convert_from_bytes(cls, elem):
        if isinstance(elem, bytes):
            elem = bytes_to_native_str(elem)
        elif isinstance(elem, list):
            elem = [cls.convert_from_bytes(e) for e in elem]
        elif isinstance(elem, dict):
            elem = OrderedDict(
                (bytes_to_native_str(n), cls.convert_from_bytes(e))
                for n, e in elem.items())
        return elem
