import os.path
import time
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


url_re = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|'
    '[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

file_path_re = re.compile(r'^(\.){0,2}\/+([\w\._\-]\/+)*[\w\._\-]')


# Holds loaded documents to avoid reloading each time
document_registry = {}


def load(url, relative_to=None, reload=False):  # @ReservedAssignment
    if isinstance(url, basestring):
        if file_path_re.match(url) is not None:
            if url.startswith('.'):
                if relative_to is None:
                    raise NineMLIOError(
                        "'relative_to' kwarg must be provided when using "
                        "relative paths (i.e. paths starting with '.'), "
                        "'{}'".format(url))
                url = os.path.abspath(os.path.join(relative_to, url))
                fle = open(url)
                mtime = time.ctime(os.path.getmtime(url))
        elif url_re.match(url) is not None:
            mtime = None  # Cannot load mtime of a general URL
            fle = urlopen
        else:
            raise NineMLIOError(
                "{} is not a valid URL or file path")
    else:
        raise NineMLIOError(
            "{} is not a valid URL (it is not even a string)"
            .format(url))
    if reload:
        document_registry.pop(url, None)
    try:
        doc, loaded_mtime = document_registry[url]
        if loaded_mtime != mtime:
            raise NineMLUpdatedFileException()
    except (KeyError, NineMLUpdatedFileException):
        doc = get_unserializer_cls(url)(fle).document
        doc._url = url
        document_registry[url] = doc, mtime

url = self._standardise_url(url)
try:
    doc_ref = self._loaded_docs[url]
    if doc_ref():
        raise NineMLRuntimeError(
            "Cannot set url of document to '{}' as there is "
            "already a document loaded in memory with that url. "
            "Please remove all references to it first (see "
            "https://docs.python.org/2/c-api/intro.html"
            "#objects-types-and-reference-counts)"
            .format(url))
except KeyError:
    pass
# Register the url with the Document class to avoid reloading

# Update the url
self._url = url


def read_url(url, relative_to=None):
    if isinstance(url, basestring):
        if file_path_re.match(url) is not None:
            if url.startswith('.'):
                if relative_to is None:
                    raise NineMLIOError(
                        "'relative_to' kwarg must be provided when using "
                        "relative paths (i.e. paths starting with '.'), '{}'"
                        .format(url))
                url = os.path.abspath(os.path.join(relative_to, url))
            fle = open(url)
        elif url_re.match(url) is not None:
            fle = urlopen(url)
        else:
            raise NineMLIOError(
                "{} is not a valid URL or file path")
    elif isinstance(url, file):
        fle = url
        url = fle.name
    else:
        raise NineMLIOError(
            "{} is not a valid URL or file handle".format(url))
    return fle, url


def write_xml(xml, filename):
    with open(filename, 'w') as f:
        etree.ElementTree(xml).write(f, encoding="UTF-8",
                                     pretty_print=True,
                                     xml_declaration=True)


def read(url, relative_to=None, name=None, **kwargs):
    """
    Read a NineML file and parse its child elements

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    if '#' in url:
        if name is not None:
            raise NineMLSerializationError(
                "Name specified both in url string ('{}') and in "
                "kwarg ('{}')".format(url, name))
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
    serializer = get_serializer(document, url, **kwargs)
    serializer.write(url, **kwargs)


def get_serializer_cls(url):
    _, ext = os.path.splitext(url)
    Serializer = ext_to_serializer[ext[1:]]
    if Serializer is None:
        raise NineMLSerializationError(
            "Was not able to import '{}' serializer, please install "
            "relevant package".format(ext[1:]))
    return Serializer


def get_unserializer_cls(url):
    _, ext = os.path.splitext(url)
    Unserializer = ext_to_unserializer[ext[1:]]
    if Unserializer is None:
        raise NineMLSerializationError(
            "Was not able to import '{}' unserializer, please install "
            "relevant package".format(ext[1:]))
    return Unserializer


ext_to_serializer = {
    'xml': XMLSerializer}


ext_to_unserializer = {
    'xml': XMLUnserializer}


#     def write(self, url, version=XML_VERSION, **kwargs):
#         if self.url is None:
#             self.url = None  # Required so relative urls can be generated
#         elif self.url != url:
#             raise NineMLRuntimeError(
#                 "Cannot write the same Document object to two different "
#                 "locations '{}' and '{}'. Please either explicitly change "
#                 "its `url` property or create a duplicate using the "
#                 "`duplicate` method before attempting to write it to the new "
#                 "location".format(self.url, url))
#         doc_xml = self.to_xml(E=get_element_maker(version), **kwargs)
#         write_xml(doc_xml, url)


#     @classmethod
#     def load(cls, xml, url=None, register_url=True, force_reload=False,
#              **kwargs):
#         """
#         Loads the lib9ml object model from a root lxml.etree.Element. If the
#         document has been previously loaded it is reused. To reload a document
#         that has been changed on file, please delete any references to it first
# 
#         Parameters
#         ----------
#         xml : etree.Element
#             The 'NineML' etree.Element to load the object model from
#         url : str
#             Specifies the url that the xml should be considered
#             to have been read from in order to resolve relative
#             references
#         register_url : bool
#             Whether to cache this loaded xml in the class dictionary
#         force_reload : bool
#             Whether to ignore existing entry in cache and force a reload of the
#             xml from file
#         """
#         if isinstance(xml, basestring):
#             xml = etree.fromstring(xml)
#         url = cls._standardise_url(url)
#         doc = cls.from_xml(xml, url=url, **kwargs)
#         if force_reload:
#             if url in cls._loaded_docs:
#                 logger.warning("Reloading '{}' URL, old references to this URL"
#                                " should not be rewritten to file"
#                                .format(url))
#                 del cls._loaded_docs[url]
#         if register_url:
#             if url is not None:
#                 # Check whether the document has already been loaded and is is
#                 # still in memory
#                 try:
#                     # Loaded docs are stored as weak refs to allow the document
#                     # to be released from memory by the garbarge collector
#                     loaded_doc_ref = cls._loaded_docs[url]
#                 except KeyError:  # If the url hasn't been loaded before
#                     loaded_doc_ref = None
#                 if loaded_doc_ref is not None:
#                     # NB: weakrefs to garbarge collected objs eval to None
#                     loaded_doc = loaded_doc_ref()
#                     if loaded_doc is not None and loaded_doc != doc:
#                         raise NineMLRuntimeError(
#                             "Cannot reuse the '{}' url for two different "
#                             "documents (NB: the file may have been modified "
#                             "externally between reads). To reload please "
#                             "remove all references to the original version "
#                             "and permit it to be garbarge collected "
#                             "(see https://docs.python.org/2/c-api/intro.html"
#                             "#objects-types-and-reference-counts): {}".format(
#                                 url, doc.find_mismatch(loaded_doc)))
#             doc.url = url
#         else:
#             doc._url = url  # Bypass registering the URL, used in testing
#         return doc



#     @url.setter
#     def url(self, url):
#         if url != self.url:
#             if url is None:
#                 raise NineMLRuntimeError(
#                     "Cannot reset a documents url to None once it has been set"
#                     "('{}') please duplicate the document instead"
#                     .format(self.url))
#             url = self._standardise_url(url)
#             try:
#                 doc_ref = self._loaded_docs[url]
#                 if doc_ref():
#                     raise NineMLRuntimeError(
#                         "Cannot set url of document to '{}' as there is "
#                         "already a document loaded in memory with that url. "
#                         "Please remove all references to it first (see "
#                         "https://docs.python.org/2/c-api/intro.html"
#                         "#objects-types-and-reference-counts)"
#                         .format(url))
#             except KeyError:
#                 pass
#             # Register the url with the Document class to avoid reloading
#             self._loaded_docs[url] = weakref.ref(self)
#             # Update the url
#             self._url = url