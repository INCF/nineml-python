from .base import BaseSerializer, BaseUnserializer


class Serializer(BaseSerializer):
    "Serializer class for the HDF5 format"

    def __call__(self, *children, **attrs):
        raise NotImplementedError


class Unserializer(BaseUnserializer):
    "Unserializer class for the HDF5 format"

    def child(self, elem, cls, n, within=None, **options):
        raise NotImplementedError

    def attr(self, elem, name, **options):
        raise NotImplementedError
