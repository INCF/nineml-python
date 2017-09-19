from __future__ import absolute_import
from future.utils import native_str_to_bytes, bytes_to_native_str, PY3
from .dict import DictSerializer, DictUnserializer
from collections import OrderedDict
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
        return yaml.dump(self._prepare_dict(serial_elem, **options),
                         Dumper=Dumper)

    def _prepare_dict(self, elem_dict, **options):
        elem_dict = self.to_elem(elem_dict, **options)
        if PY3:
            elem_dict = self.convert_to_bytes(elem_dict)
        return elem_dict

    @classmethod
    def convert_to_bytes(cls, elem_dict):
        if isinstance(cls, str):
            elem_dict = native_str_to_bytes(elem_dict)
        elif isinstance(elem_dict, OrderedDict):
            elem_dict = OrderedDict(
                (n, cls.convert_to_bytes(e)) for n, e in elem_dict.items())
        return elem_dict


class YAMLUnserializer(DictUnserializer):
    """
    A Unserializer class that unserializes YAML
    """

    def from_file(self, file, **options):
        return self._finalise_dict(yaml.load(file, Loader=Loader), **options)

    def from_str(self, string, **options):
        return self._finalise_dict(yaml.load(string, Loader=Loader), **options)

    def _finalise_dict(self, elem_dict, **options):
        elem_dict = self.from_elem(elem_dict, **options)
        if PY3:
            elem_dict = self.convert_from_bytes(elem_dict)
        return elem_dict

    @classmethod
    def convert_from_bytes(cls, serial_elem):
        if isinstance(cls, str):
            serial_elem = bytes_to_native_str(serial_elem)
        elif isinstance(serial_elem, OrderedDict):
            serial_elem = OrderedDict(
                (n, cls.convert_from_bytes(e)) for n, e in serial_elem.items())
        return serial_elem
