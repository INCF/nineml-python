from builtins import zip
import h5py
from . import NINEML_BASE_NS
from tempfile import mkstemp
import contextlib
import nineml
from itertools import chain, repeat
from nineml.exceptions import (NineMLSerializationError,
                               NineMLSerializationNotSupportedError,
                               NineMLMissingSerializationError)
from nineml.serialization.base import (
    BaseSerializer, BaseUnserializer)
from nineml.exceptions import NineMLNameError
from nineml.utils import is_file_handle


class HDF5Serializer(BaseSerializer):
    """
    A Serializer class that serializes to the HDF5 format
    """

    def __init__(self, fname, **kwargs):  # @UnusedVariable @IgnorePep8 @ReservedAssignment
        if is_file_handle(fname):
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
                parent[name].attrs[self.MULT_ATTR] = True
            # Add a new group named by the next available index
            new_index = len(parent[name])
            elem = parent[name].create_group(str(new_index))
        else:
            if name in parent:
                raise NineMLSerializationError(
                    "'{}' already exists in parent ({}) when creating "
                    "singleton element".format(name, parent))
            elem = parent.create_group(name)
            elem.attrs[self.MULT_ATTR] = False
        if namespace is not None:
            elem.attrs[self.NS_ATTR] = namespace
        return elem

    def create_root(self, **options):  # @UnusedVariable
        root = self._file.create_group(nineml.Document.nineml_type)
        root.attrs[self.NS_ATTR] = self.nineml_namespace
        return root

    def set_attr(self, serial_elem, name, value, **options):  # @UnusedVariable
        serial_elem.attrs[name] = value

    def set_body(self, serial_elem, value, **options):  # @UnusedVariable @IgnorePep8
        self.set_attr(serial_elem, self.BODY_ATTR, value, **options)

    def to_file(self, serial_elem, file, **options):  # @UnusedVariable  @IgnorePep8 @ReservedAssignment
        if file.name != self._file.filename:
            raise NineMLSerializationError(
                "Can only write elems to the file that is named in the "
                "__init__ method as the file is written to as the elements "
                "are serialized.")

    def to_str(self, serial_elem, **options):  # @UnusedVariable  @IgnorePep8
        raise NineMLSerializationNotSupportedError(
            "'HDF5' format cannot be converted to a string")

    def to_elem(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem


class HDF5Unserializer(BaseUnserializer):
    """
    A Unserializer class unserializes the HDF5 format.
    """

    def get_child(self, parent, nineml_type, **options):  # @UnusedVariable
        try:
            elem = parent[nineml_type]
        except KeyError:
            raise NineMLMissingSerializationError(
                "{} doesn't have a '{}' child".format(parent, nineml_type))
        if elem.attrs[self.MULT_ATTR]:
            raise NineMLSerializationError(
                "'{}' is a multiple element within {}"
                .format(nineml_type, parent))
        return elem

    def get_children(self, parent, nineml_type, **options):  # @UnusedVariable
        try:
            children = parent[nineml_type]
        except KeyError:
            return iter([])
        if not children.attrs[self.MULT_ATTR]:
            raise NineMLSerializationError(
                "'{}' is not a multiple element within {}"
                .format(nineml_type, parent))
        return iter(children.values())

    def get_all_children(self, parent, **options):  # @UnusedVariable
        return chain(
            ((n, e) for n, e in parent.items() if not e.attrs[self.MULT_ATTR]),
            *(zip(repeat(n), iter(e.values())) for n, e in parent.items()
              if e.attrs[self.MULT_ATTR]))

    def get_attr(self, serial_elem, name, **options):  # @UnusedVariable
        return serial_elem.attrs[name]

    def get_body(self, serial_elem, **options):  # @UnusedVariable
        try:
            return serial_elem.attrs[self.BODY_ATTR]
        except KeyError:
            return None

    def get_attr_keys(self, serial_elem, **options):  # @UnusedVariable
        return iter(serial_elem.attrs.keys())

    def get_namespace(self, serial_elem, **options):  # @UnusedVariable
        try:
            ns = self.get_attr(serial_elem, self.NS_ATTR, **options)
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

    def from_elem(self, serial_elem, **options):  # @UnusedVariable
        return serial_elem
