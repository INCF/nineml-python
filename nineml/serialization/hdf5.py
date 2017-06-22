import h5py
from . import NINEML_BASE_NS
from tempfile import mkstemp
import contextlib
import nineml
from itertools import chain, izip, repeat
from nineml.exceptions import (NineMLSerializationError,
                               NineMLSerializationNotSupportedError)
from .base import BaseSerializer, BaseUnserializer, BODY_ATTR, NS_ATTR
from nineml.exceptions import NineMLNameError


class HDF5Serializer(BaseSerializer):
    """
    A Serializer class that serializes to the HDF5 format
    """

    def __init__(self, fname, **kwargs):  # @UnusedVariable @IgnorePep8 @ReservedAssignment
        if isinstance(fname, file):
            # Close the file and reopen with the h5py File object
            file_ = fname
            fname = file_.name
            file_.close()
        self._file = h5py.File(fname, 'w')
        super(HDF5Serializer, self).__init__(**kwargs)

    def create_elem(self, name, parent, namespace=None, multiple=False,
                    **options):  # @UnusedVariable @IgnorePep8
        if multiple:
            if name not in parent:
                parent.create_group(name)
            # Add a new group named by the next available index
            new_index = len(parent[name])
            parent[name].create_group(str(new_index))
        else:
            if name in parent:
                raise NineMLSerializationError(
                    "'{}' already exists in parent ({}) when creating "
                    "singleton element".format(name, parent))
            elem = parent.create_group(name)
        if namespace is not None:
            self.set_attr(elem, NS_ATTR, namespace, **options)
        return elem

    def create_root(self, **options):  # @UnusedVariable
        return self._file.create_group(nineml.Document.nineml_type)

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem.attrs[name] = value

    def set_body(self, serial_elem, value, sole=False, **options):  # @UnusedVariable @IgnorePep8
        self.set_attr(serial_elem, BODY_ATTR, value, **options)

    def to_file(self, serial_elem, file, **options):  # @UnusedVariable  @IgnorePep8 @ReservedAssignment
        if file.name != self._file.name:
            raise NineMLSerializationError(
                "Can only write elems to the file that is named in the "
                "__init__ method as the file is written to as the elements "
                "are serialized.")

    def to_str(self, serial_elem, **options):  # @UnusedVariable  @IgnorePep8
        raise NineMLSerializationNotSupportedError(
            "'HDF5' format cannot be converted to a string")


class HDF5Unserializer(BaseUnserializer):
    """
    A Unserializer class unserializes the HDF5 format.
    """

    def get_children(self, serial_elem, **options):  # @UnusedVariable
        return chain(
            ((n, e) for n, e in serial_elem.iteritems()
             if isinstance(e, dict)),
            *(izip(repeat(n), e) for n, e in serial_elem.iteritems()
              if isinstance(e, list)))

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        return serial_elem.attrs[name]

    def get_body(self, serial_elem, sole=True, **options):  # @UnusedVariable
        return serial_elem.attrs[BODY_ATTR]

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem.attrs.iterkeys()

    def get_namespace(self, serial_elem, **options):  # @UnusedVariable
        try:
            ns = self.get_attr(serial_elem, NS_ATTR, **options)
        except NineMLNameError:
            ns = NINEML_BASE_NS + self.version
        return ns

    def from_file(self, file, **options):  # @UnusedVariable @ReservedAssignment @IgnorePep8
        # Close the file and reopen in h5py File object
        fname = file.name
        file.close()
        return h5py.File(fname)[nineml.Document.nineml_type]

    def from_urlfile(self, urlfile, **options):  # @UnusedVariable
        # Cache URL to temporary file and open in h5py File object
        f, fname = mkstemp()
        with contextlib.closing(f):
            f.write(urlfile.read())
        return h5py.File(fname)[nineml.Document.nineml_type]

    def from_str(self, string, **options):
        raise NineMLSerializationNotSupportedError(
            "'HDF5' format cannot be read from a string")
