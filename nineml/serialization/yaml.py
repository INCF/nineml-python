from __future__ import absolute_import
from .dict import DictSerializer, DictUnserializer
from collections import OrderedDict
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper  # @UnusedImport
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

Dumper.add_representer(OrderedDict, dict_representer)
Loader.add_constructor(_mapping_tag, dict_constructor)


class YAMLSerializer(DictSerializer):
    """
    A Serializer class that serializes to YAML
    """

    def to_file(self, serial_elem, file, **options):  # @UnusedVariable  @IgnorePep8 @ReservedAssignment
        yaml.dump(self.to_elem(serial_elem), stream=file, Dumper=Dumper)

    def to_str(self, serial_elem, **options):  # @UnusedVariable  @IgnorePep8
        return yaml.dump(self.to_elem(serial_elem), Dumper=Dumper)


class YAMLUnserializer(DictUnserializer):
    """
    A Unserializer class that unserializes YAML
    """

    def from_file(self, file, **options):  # @ReservedAssignment @UnusedVariable @IgnorePep8
        return self.from_elem(yaml.load(file, Loader=Loader))

    def from_str(self, string, **options):  # @UnusedVariable
        return self.from_elem(yaml.load(string, Loader=Loader))
