import nineml
import os.path
from nineml.exceptions import NineMLSerializationError
try:
    from .xml import (
        Serializer as XMLSerializer, Unserializer as XMLUnserializer)
except:
    XMLSerializer = None
    XMLUnserializer = None


def read(url, relative_to=None, name=None, **kwargs):
    """
    Read a NineML file and parse its child elements

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    if '#' in url:
        url, name = url.split('#')
    xml, url = read_xml(url, relative_to=relative_to)
    root = xml.getroot()
    doc = Document.load(root, url, **kwargs)
    if name is None:
        model = doc
    else:
        model = doc[name]
    return model


def write(nineml_object, url, **kwargs):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
    """
    # Encapsulate the NineML element in a document if it is not already
    if not isinstance(nineml_object, nineml.Document):
        document = nineml.Document(nineml_object, **kwargs)
    serializer = get_serializer(url)
    elem = serializer.serialize()
    document.write(filename, **kwargs)


def get_serializer(url):
    _, ext = os.path.splitext(url)
    Serializer = ext_to_serializer[ext[1:]]
    if Serializer is None:
        raise NineMLSerializationError(
            "Was not able to import '{}' serializer, please install "
            "relevant package".format(ext[1:]))
    return Serializer(url=url)


def get_unserializer(url):
    _, ext = os.path.splitext(url)
    Unserializer = ext_to_unserializer[ext[1:]]
    if Unserializer is None:
        raise NineMLSerializationError(
            "Was not able to import '{}' unserializer, please install "
            "relevant package".format(ext[1:]))
    return Unserializer(url=url)


ext_to_serializer = {
    'xml': XMLSerializer}


ext_to_unserializer = {
    'xml': XMLUnserializer}
