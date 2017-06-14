from nineml.exceptions import NineMLSerializationNotSupportedError
from . import NINEML_BASE_NS
from .base import BaseSerializer, BaseUnserializer, BODY_ATTR, NS_ATTR
from nineml.exceptions import NineMLNameError


def value_str(value):
    # Ensure all decimal places are preserved for floats
    return repr(value) if isinstance(value, float) else str(value)


class DictSerializer(BaseSerializer):
    """
    A Serializer class that serializes to a dictionary of lists and attributes.
    Is used as the base class for the Pickle, JSON and YAML serializers
    """

    def create_elem(self, name, parent, namespace=None, **options):  # @UnusedVariable @IgnorePep8
        parent[name] = {}

    def create_root(self, **options):  # @UnusedVariable
        return {}

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem[name] = value

    def set_body(self, serial_elem, value, **options):  # @UnusedVariable @IgnorePep8
        self.setattr(serial_elem, BODY_ATTR, value, **options)

    def to_file(self, serial_elem, file, **options):  # @UnusedVariable  @IgnorePep8 @ReservedAssignment
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be written to file")

    def to_str(self, serial_elem, **options):  # @UnusedVariable  @IgnorePep8
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be converted to a string")


class DictUnserializer(BaseUnserializer):
    """
    A Unserializer class that serializes to a dictionary of lists and
    attributes. Is used as the base class for the Pickle, JSON and YAML
    serializers
    """

    def __init__(self, root, version, **kwargs):
        super(DictUnserializer, self).__init__(root, version, **kwargs)

    def get_children(self, serial_elem, **options):  # @UnusedVariable
        return ((n, e) for n, e in serial_elem.iteritems()
                if self._is_child(e))

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        try:
            value = serial_elem[name]
        except KeyError:
            raise NineMLNameError(
                "Element {} doesn't contain an '{}' attribute"
                .format(serial_elem, name))
        if self._is_child(value):
            raise NineMLNameError(
                "Element {} contains a '{}' child ({}) not an attribute"
                .format(serial_elem, name, value))
        return value

    def get_body(self, serial_elem, **options):  # @UnusedVariable
        self.get_attr(serial_elem, BODY_ATTR)

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        return (n for n, e in serial_elem.iteritems()
                if not self._is_child(e))

    def get_namespace(self, serial_elem, **options):  # @UnusedVariable
        try:
            self.get_attr(serial_elem, NS_ATTR, **options)
        except NineMLNameError:
            return NINEML_BASE_NS + self.version

    def from_file(self, file, **options):  # @ReservedAssignment
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be written to file")

    def from_str(self, string, **options):
        raise NineMLSerializationNotSupportedError(
            "'dict' format cannot be written to file")

    @classmethod
    def _is_child(cls, elem):
        return isinstance(elem, (dict, list))
