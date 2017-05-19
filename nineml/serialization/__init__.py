import os.path
import re
import time
from urllib import urlopen
import weakref
import contextlib
from nineml.exceptions import (
    NineMLSerializationError, NineMLIOError, NineMLUpdatedFileException)

NINEML_BASE_NS = "http://nineml.net/9ML/"
NINEML_V1_NS = NINEML_BASE_NS + '1.0'
NINEML_V2_NS = NINEML_BASE_NS + '2.0'
NINEML_NS = NINEML_V1_NS
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
UNCERTML_NS = "http://www.uncertml.org/2.0"

import nineml  # @IgnorePep8
try:
    from .xml import (
        Serializer as XMLSerializer, Unserializer as XMLUnserializer)
except:
    XMLUnserializer = XMLSerializer = None


ext_to_serializer = {
    'xml': XMLSerializer}


ext_to_unserializer = {
    'xml': XMLUnserializer}


def read(url, **kwargs):
    if file_path_re.match(url) is not None:
        handle = open(url)
    elif url_re.match(url) is not None:
        handle = urlopen(url)
    else:
        raise NineMLIOError(
            "Unrecognised url '{}'".format(url))
    # Get the unserializer based on the url extension
    Unserializer = ext_to_unserializer[ext_from_url(url)]
    with contextlib.closing(handle):
        return Unserializer(handle, url=url).unserialize(**kwargs)


def write(nineml_object, url, **kwargs):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
    """
    # Encapsulate the NineML element in a document if it is not already
    if not isinstance(nineml_object, nineml.Document):
        document = nineml.Document(nineml_object, **kwargs)
    elif document.url is not None and document.url != url:
        document = document.clone()
    Serializer = ext_to_serializer[ext_from_url(url)]
    with open(url) as f:
        Serializer(document, url, **kwargs).write(f, **kwargs)
    document._url = url
    nineml.Document.registry[url] = (weakref.ref(document),
                                     time.ctime(os.path.getmtime(url)))


def ext_from_url(url):
    if '#' in url:
        url = url.split('#')[0]
    return os.path.splitext(url)[-1][1:]


url_re = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|'
    '[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

file_path_re = re.compile(r'^(\.){0,2}\/+([\w\._\-]\/+)*[\w\._\-]')
