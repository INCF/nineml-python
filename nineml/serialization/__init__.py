from future import standard_library
standard_library.install_aliases()
from past.builtins import basestring  # @IgnorePep8
import os.path  # @IgnorePep8
import re  # @IgnorePep8
import time  # @IgnorePep8
import weakref  # @IgnorePep8
from urllib.request import urlopen  # @IgnorePep8
import contextlib  # @IgnorePep8
from nineml.base import DocumentLevelObject  # @IgnorePep8
from nineml.document import Document  # @IgnorePep8
from nineml.exceptions import (  # @IgnorePep8
    NineMLSerializationError, NineMLIOError, NineMLReloadDocumentException,
    NineMLSerializerNotImportedError)

DEFAULT_VERSION = 1
DEFAULT_FORMAT = 'xml'  # see nineml.serialization format_to_serializer.keys()

NINEML_BASE_NS = "http://nineml.net/9ML/"
NINEML_V1_NS = NINEML_BASE_NS + '1.0'
NINEML_V2_NS = NINEML_BASE_NS + '2.0'
if DEFAULT_VERSION == 1:
    NINEML_NS = NINEML_V1_NS
else:
    NINEML_NS = NINEML_V2_NS
ALL_NINEML_NS = [NINEML_V1_NS, NINEML_V2_NS]
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
UNCERTML_NS = "http://www.uncertml.org/2.0"

import nineml  # @IgnorePep8
from .dict import DictSerializer, DictUnserializer  # @IgnorePep8
from .json import JSONSerializer, JSONUnserializer  # @IgnorePep8
try:
    from .xml import XMLSerializer, XMLUnserializer
except ImportError:
    XMLSerializer = XMLUnserializer = None
try:
    from .yaml import YAMLSerializer, YAMLUnserializer
except ImportError:
    YAMLSerializer = YAMLUnserializer = None
try:
    from .hdf5 import HDF5Serializer, HDF5Unserializer
except ImportError:
    HDF5Serializer = HDF5Unserializer = None


ext_to_format = {
    '.xml': 'xml',
    '.yml': 'yaml',
    '.h5': 'hdf5',
    '.json': 'json'}

format_to_serializer = {
    'xml': XMLSerializer,
    'dict': DictSerializer,
    'yaml': YAMLSerializer,
    'json': JSONSerializer,
    'hdf5': HDF5Serializer}


format_to_unserializer = {
    'xml': XMLUnserializer,
    'dict': DictUnserializer,
    'yaml': YAMLUnserializer,
    'json': JSONUnserializer,
    'hdf5': HDF5Unserializer}


def read(url, relative_to=None, reload=False, register=True, **kwargs):  # @ReservedAssignment @IgnorePep8
    """
    Reads a NineML document from the given url or file system path and returns
    a Document object.

    Parameters
    ----------
    url : str
        An url or path on the local file system (either absoluate or relative).
        The format the file is read-from/written-to is determined by the
        extension of the url/filename.  If a '#' is in the ``url`` string then
        the part of the string after the '#' is treated as the name of the
        object to return from the Document.
    relative_to : URL | None
        The URL/file path to resolve relative file paths from
    reload : bool
        Whether to reload the document from file if it is already in the cache
        or not.
    register : bool
        Whether to store the document in the cache after it is read
    """
    if not isinstance(url, basestring):
        raise NineMLIOError(
            "{} is not a valid URL (it is not even a string)"
            .format(url))
    if '#' in url:
        url, name = url.split('#')
    else:
        name = None
    if file_path_re.match(url) is not None:
        if url.startswith('.'):
            if relative_to is None:
                relative_to = os.getcwd()
            url = os.path.abspath(os.path.join(relative_to, url))
        mtime = time.ctime(os.path.getmtime(url))
    elif url_re.match(url) is not None:
        mtime = None  # Cannot load mtime of a general URL
    else:
        raise NineMLIOError(
            "{} is not a valid URL or file path (NB: relative file paths must "
            "start with './')".format(url))
    if reload:
        nineml.Document.registry.pop(url, None)
    try:  # Try to use cached document in registry
        doc_ref, loaded_mtime = nineml.Document.registry[url]
        if loaded_mtime != mtime or doc_ref() is None or not register:
            raise NineMLReloadDocumentException()
        doc = doc_ref()
    except (KeyError, NineMLReloadDocumentException):  # Reload from file
        # Get the unserializer based on the url extension
        format = format_from_url(url)  # @ReservedAssignment
        try:
            Unserializer = format_to_unserializer[format]
        except KeyError:
            raise NineMLSerializationError(
                "Unrecognised format '{}' in url '{}', can be one of '{}'"
                .format(format, url,
                        "', '".join(list(format_to_unserializer.keys()))))
        if Unserializer is None:
            raise NineMLSerializerNotImportedError(
                "Cannot write to '{}' as {} serializer cannot be imported. "
                "Please check the required dependencies are correctly "
                "installed".format(url, format))
        if file_path_re.match(url) is not None:
            file = open(url)  # @ReservedAssignment
        elif url_re.match(url) is not None:
            file = urlopen(url)  # @ReservedAssignment
        else:
            raise NineMLIOError(
                "Unrecognised url '{}'".format(url))
        with contextlib.closing(file):
            doc = Unserializer(root=file, url=url, **kwargs).unserialize()
        if register:
            nineml.Document.registry[url] = weakref.ref(doc), mtime
    if name is not None:
        nineml_obj = doc[name]
    else:
        nineml_obj = doc
    return nineml_obj


def write(url, *nineml_objects, **kwargs):
    """
    Writes NineML objects or single document to file given by a path

    Parameters
    ----------
    url : str
        A path on the local file system (either absoluate or relative).
        The format for the serialization is written in is determined by the
        extension of the url.
    register : bool
        Whether to store the document in the cache after writing
    version : str | float | int
        The version to serialize the NineML objects to
    """
    register = kwargs.pop('register', True)
    # Encapsulate the NineML element in a document if it is not already
    if len(nineml_objects) == 1 and isinstance(nineml_objects[0],
                                               nineml.Document):
        document = nineml_objects[0]
        if document.url is not None and document.url != url:
            document = document.clone()
    else:
        document = nineml.Document(*nineml_objects, **kwargs)
    format = format_from_url(url)  # @ReservedAssignment
    try:
        Serializer = format_to_serializer[format]
    except KeyError:
        raise NineMLSerializationError(
            "Unrecognised format '{}' in url '{}', can be one of '{}'"
            .format(format, url,
                    "', '".join(list(format_to_serializer.keys()))))
    if Serializer is None:
        raise NineMLSerializerNotImportedError(
            "Cannot write to '{}' as {} serializer cannot be "
            "imported. Please check the required dependencies are correctly "
            "installed".format(url, format))
    with Serializer.open_file(url) as file:  # @ReservedAssignment
        # file is passed to the serializer for serializations that store
        # elements dynamically, such as HDF5
        serializer = Serializer(document=document, fname=file, **kwargs)
        serializer.serialize()
        serializer.to_file(serializer.root, file, **kwargs)
    if register:
        document._url = url
        nineml.Document.registry[url] = (weakref.ref(document),
                                         time.ctime(os.path.getmtime(url)))


def serialize(nineml_object, format=DEFAULT_FORMAT, version=DEFAULT_VERSION,  # @ReservedAssignment @IgnorePep8
              document=None, to_str=False, **kwargs):
    """
    Serializes a NineML object into a serialized element

    Parameters
    ----------
    nineml_object : BaseNineMLObject
        The object to serialize
    format : str
        The name of the format (which matches a key format_to_serializer)
    version : str | float | int
        The version to serialize the NineML objects to
    document : Document
        The document to write local references to
    to_str : bool
        To serialize to a string instead of a serial element.
    """
    if isinstance(nineml_object, nineml.Document):
        if document is not None and document is not nineml_object:
            raise NineMLSerializationError(
                "Supplied 'document' kwarg ({}) is not the same as document to"
                " serialize ({})".format(document, nineml_object))
        document = nineml_object
    Serializer = format_to_serializer[format]
    if isinstance(nineml_object, DocumentLevelObject) and document is None:
        document = Document(nineml_object)
    serializer = Serializer(version=version, document=document, **kwargs)
    serial_elem = serializer.visit(nineml_object, **kwargs)
    if to_str:
        serialized = serializer.to_str(serial_elem,
                                        nineml_type=nineml_object.nineml_type,
                                        **kwargs)
    else:
        serialized = serializer.to_elem(serial_elem,
                                        nineml_type=nineml_object.nineml_type,
                                        **kwargs)
    return serialized


def unserialize(serial_elem, nineml_cls, format, version,  # @ReservedAssignment @IgnorePep8
                root=None, url=None, document=None, **kwargs):
    """
    Unserializes a serial element to the given NineML class

    Parameters
    ----------
    serial_elem : <serial-element>
        A serial element in the format given
    nineml_cls : type
        The class to attempt to unserialize the serial element to
    format : str
        The name of the format (which matches a key format_to_serializer)
    version : str | float | int
        The version to serialize the NineML objects to
    document : Document | None
        The document to read local references from
    url : URL | None
        The url to assign to the unserialized object
    root : <serial-element>
        A serial element of containing the document to read local references
        from
    """
    Unserializer = format_to_unserializer[format]
    unserializer = Unserializer(version=version, root=root,
                                url=url, document=document)
    if isinstance(serial_elem, basestring):
        serial_elem = unserializer.from_str(serial_elem,
                                            nineml_type=nineml_cls.nineml_type,
                                            **kwargs)
    else:
        serial_elem = unserializer.from_elem(
            serial_elem, nineml_type=nineml_cls.nineml_type, **kwargs)
    return unserializer.visit(serial_elem, nineml_cls, **kwargs)


def format_from_url(url):
    if '#' in url:
        url = url.split('#')[0]
    return ext_to_format[os.path.splitext(url)[-1]]


url_re = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|'
    '[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

file_path_re = re.compile(r'^(\.){0,2}\/+([\w\._\-]\/+)*[\w\._\-]')
