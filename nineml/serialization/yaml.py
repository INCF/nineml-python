from __future__ import absolute_import
from future.utils import native_str_to_bytes, bytes_to_native_str
from .dict import DictSerializer, DictUnserializer
from collections import OrderedDict
from .base.visitors import BaseVisitor, BaseSerializer
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

    NS_ATTR = BaseSerializer.sanitize_str(BaseVisitor.NS_ATTR)
    BODY_ATTR = BaseSerializer.sanitize_str(BaseVisitor.BODY_ATTR)

    def create_elem(self, name, parent, namespace=None, multiple=False,  # @UnusedVariable @IgnorePep8
                    **options):
        return super(YAMLSerializer, self).create_elem(
            native_str_to_bytes(name), parent, namespace=namespace,
            multiple=multiple, **options)

    def to_file(self, serial_elem, file, **options):  # @UnusedVariable  @IgnorePep8 @ReservedAssignment
        yaml.dump(self.to_elem(serial_elem, **options), stream=file,
                  Dumper=Dumper)

    def to_str(self, serial_elem, **options):  # @UnusedVariable  @IgnorePep8
        return yaml.dump(self.to_elem(serial_elem, **options), Dumper=Dumper)

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        super(YAMLSerializer, self).set_attr(serial_elem, name,
                                             self.sanitize_str(value),
                                             **options)

    def set_body(self, serial_elem, value, **options):  # @UnusedVariable @IgnorePep8
        super(YAMLSerializer, self).set_body(
            serial_elem, self.sanitize_str(value), **options)


class YAMLUnserializer(DictUnserializer):
    """
    A Unserializer class that unserializes YAML
    """

    def from_file(self, file, **options):  # @ReservedAssignment @UnusedVariable @IgnorePep8
        return self.from_elem(yaml.load(file, Loader=Loader), **options)

    def from_str(self, string, **options):  # @UnusedVariable
        return self.from_elem(yaml.load(string, Loader=Loader), **options)

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        return self.sanitize_str(super(YAMLUnserializer, self).get_attr(
            serial_elem, name, **options))

    def get_body(self, serial_elem, **options):  # @UnusedVariable
        return self.sanitize_str(super(YAMLUnserializer, self).get_body(
            serial_elem, **options))

    def get_all_children(self, parent, **options):  # @UnusedVariable
        return ((bytes_to_native_str(t), e)
                for t, e in super(YAMLUnserializer, self).get_all_children(
                    parent, **options))
