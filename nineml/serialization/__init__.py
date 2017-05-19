import os.path
import nineml
import re
from urllib import urlopen
import weakref
import contextlib
from nineml.exceptions import (
    NineMLSerializationError, NineMLIOError, NineMLUpdatedFileException)
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
    Serializer = ext_to_serializer[ext_from_url(url)]
    with open(url) as f:
        Serializer(document, url, **kwargs).write(f, **kwargs)


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
