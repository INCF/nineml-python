import os.path
import re
import time
import weakref
from urllib import urlopen
import contextlib
from nineml.exceptions import (
    NineMLSerializationError, NineMLIOError, NineMLReloadDocumentException)

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
from .pickle import PickleSerializer, PickleUnserializer  # @IgnorePep8
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
    '.json': 'json',
    '.pkl': 'pickle'}

format_to_serializer = {
    'xml': XMLSerializer,
    'dict': DictSerializer,
    'yaml': YAMLSerializer,
    'json': JSONSerializer,
    'pickle': PickleSerializer,
    'hdf5': HDF5Serializer}


format_to_unserializer = {
    'xml': XMLUnserializer,
    'dict': DictUnserializer,
    'yaml': YAMLUnserializer,
    'json': JSONUnserializer,
    'pickle': PickleUnserializer,
    'hdf5': HDF5Unserializer}


def read(url, relative_to=None, reload=False, register=True, **kwargs):  # @ReservedAssignment @IgnorePep8
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
            "{} is not a valid URL or file path".format(url))
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
                        "', '".join(format_to_unserializer.keys())))
        if Unserializer is None:
            raise NineMLSerializationError(
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
            try:
                doc = Unserializer(root=file, url=url, **kwargs).unserialize()
            except:
                raise
        if register:
            nineml.Document.registry[url] = weakref.ref(doc), mtime
    if name is not None:
        nineml_obj = doc[name]
    else:
        nineml_obj = doc
    return nineml_obj


def write(url, *nineml_objects, **kwargs):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
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
            .format(format, url, "', '".join(format_to_serializer.keys())))
    if Serializer is None:
        raise NineMLSerializationError(
            "Cannot write to '{}' as {} serializer cannot be "
            "imported. Please check the required dependencies are correctly "
            "installed".format(url, format))
    with open(url, 'w') as file:  # @ReservedAssignment
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
              document=None, **kwargs):
    if isinstance(nineml_object, nineml.Document):
        if document is not None and document is not nineml_object:
            raise NineMLSerializationError(
                "Supplied 'document' kwarg ({}) is not the same as document to"
                " serialize ({})".format(document, nineml_object))
        document = nineml_object
    Serializer = format_to_serializer[format]
    serializer = Serializer(version=version, document=document)
    return serializer.visit(nineml_object, **kwargs)


def unserialize(serial_elem, nineml_cls, format, version,  # @ReservedAssignment @IgnorePep8
                root=None, url=None, document=None, **kwargs):
    Unserializer = format_to_unserializer[format]
    unserializer = Unserializer(version=version, root=root,
                                url=url, document=document)
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
