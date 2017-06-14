from nineml.document import Document
from nineml.exceptions import (NineMLSerializationError,
                               NineMLSerializationNotSupportedError)
from .base import BaseSerializer, BaseUnserializer
from nineml.exceptions import NineMLNameError


def value_str(value):
    # Ensure all decimal places are preserved for floats
    return repr(value) if isinstance(value, float) else str(value)


class PickleSerializer(BaseSerializer):
    """
    A Serializer class that serializes to a dictionary of lists and attributes.
    Is used as the base class for the Pickle, JSON and YAML serializers
    """

    def create_elem(self, name, parent, namespace=None, **options):  # @UnusedVariable @IgnorePep8
        pass

    def create_root(self, **options):  # @UnusedVariable
        pass

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        pass

    def set_body(self, serial_elem, value, sole=False, **options):  # @UnusedVariable @IgnorePep8
        pass

    def to_file(self, serial_elem, file, **options):  # @UnusedVariable  @IgnorePep8 @ReservedAssignment
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be written to file")

    def to_str(self, serial_elem, **options):  # @UnusedVariable  @IgnorePep8
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be converted to a string")


class PickleUnserializer(BaseUnserializer):
    """
    A Unserializer class that serializes to a dictionary of lists and
    attributes. Is used as the base class for the Pickle, JSON and YAML
    serializers
    """

    def get_children(self, serial_elem, **options):  # @UnusedVariable
        pass

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        pass

    def get_body(self, serial_elem, sole=True, **options):  # @UnusedVariable
        pass

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        pass

    def get_namespace(self, serial_elem, **options):  # @UnusedVariable
        pass

    def from_file(self, file, **options):  # @ReservedAssignment
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be written to file")

    def from_str(self, string, **options):
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be written to file")