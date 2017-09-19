from __future__ import absolute_import
import json
from .dict import DictSerializer, DictUnserializer


class JSONSerializer(DictSerializer):
    """
    A Serializer class that serializes to JSON
    """

    def to_file(self, serial_elem, file, skipkeys=False, ensure_ascii=True, #   @IgnorePep8 @ReservedAssignment
                check_circular=True, allow_nan=True, cls=None, indent=None,
                separators=None, default=None,
                sort_keys=False, **options):  # @UnusedVariable
        json.dump(self.to_elem(serial_elem, **options), file,
                  skipkeys=skipkeys,
                  ensure_ascii=ensure_ascii, check_circular=check_circular,
                  allow_nan=allow_nan, cls=cls, indent=indent,
                  separators=separators, default=default,
                  sort_keys=sort_keys)

    def to_str(self, serial_elem, skipkeys=False, ensure_ascii=True,
                check_circular=True, allow_nan=True, cls=None, indent=None,
                separators=None, default=None,
                sort_keys=False, **options):  # @UnusedVariable  @IgnorePep8
        return json.dumps(self.to_elem(serial_elem, **options),
                          skipkeys=skipkeys, ensure_ascii=ensure_ascii,
                          check_circular=check_circular, allow_nan=allow_nan,
                          cls=cls, indent=indent, separators=separators,
                          default=default, sort_keys=sort_keys)

    @classmethod
    def open_file(cls, url):
        return open(url, 'w')


class JSONUnserializer(DictUnserializer):
    """
    A Unserializer class that unserializes JSON
    """

    def from_file(self, file, encoding=None, **options):  # @ReservedAssignment @UnusedVariable @IgnorePep8
        return self.from_elem(json.load(file, encoding=encoding), **options)

    def from_str(self, string, encoding=None, **options):  # @UnusedVariable
        return self.from_elem(json.loads(string, encoding=encoding), **options)
