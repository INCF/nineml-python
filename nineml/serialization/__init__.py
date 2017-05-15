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
    serializer = get_serializer(document, url, **kwargs)
    serializer.write(url, **kwargs)


def get_serializer(document, url):
    _, ext = os.path.splitext(url)
    Serializer = ext_to_serializer[ext[1:]]
    if Serializer is None:
        raise NineMLSerializationError(
            "Was not able to import '{}' serializer, please install "
            "relevant package".format(ext[1:]))
    return Serializer(document, url=url)


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