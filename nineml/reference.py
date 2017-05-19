import os
from copy import copy
from .base import AnnotatedNineMLObject
from nineml.exceptions import NineMLRuntimeError


class BaseReference(AnnotatedNineMLObject):

    """
    Base class for references to model components that are defined in the
    abstraction layer.
    """

    defining_attributes = ('url', '_referred_to')

    def __init__(self, name, document, url=None):
        super(BaseReference, self).__init__()
        document_url = document.url if document is not None else None
        if url is not None and url != document_url:
            if url.startswith('.'):
                if document_url is None:
                    raise NineMLRuntimeError(
                        "Must supply a document with a non-None URL that is "
                        "being referenced from if definition is a relative URL"
                        " string, '{}'".format(url))
                relative_to = os.path.dirname(document.url)
            else:
                relative_to = None
            remote_doc = nineml.read(url, relative_to=relative_to)
        else:
            remote_doc = document
        self._referred_to = remote_doc[name]

    @property
    def url(self):
        return self._referred_to.url

    @property
    def key(self):
        return (self._referred_to.key +
                self.url if self.url is not None else '')

    def equals(self, other, **kwargs):
        """
        Parameters
        ----------
        other : BaseReference
            The other object to determine equality with
        ignore_none_urls : bool
            A bit of a hack to ignore urls that are None (i.e. defined inline)
            during unittesting.
        """
        if not isinstance(other, self.__class__):
            return False
        return (self._referred_to == other._referred_to and
                self.url == other.url and
                self.annotations_equal(other, **kwargs))

    def __hash__(self):
        return (hash(self.__class__) ^ hash(self._referred_to.name) ^
                hash(self.url))

    def __repr__(self):
            return ('{}(name="{}"{})'
                    .format(self.__class__.__name__, self._referred_to.name,
                            ' in "{}"'.format(self.url) if self.url else ''))

    def serialize_node(self, node, **options):  # @UnusedVariable
        name = self._referred_to.name
        node.attr('name', name, **options)
        if self.url is not None and self.url != node.document.url:
            node.attr('url', self.url, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        name = node.attr('name', **options)
        url = node.attr('url', default=None, **options)
        return cls(name=name, document=node.document, url=url)

    def serialize_node_v1(self, node, **options):  # @UnusedVariable
        name = self._referred_to.name
        node.body(name, sole=False, **options)
        if self.url is not None and self.url != node.document.url:
            node.attr('url', self.url, **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):  # @UnusedVariable
        name = node.body(sole=False, **options)
        url = node.attr('url', default=None, **options)
        return cls(name=name, document=node.document, url=url)


class Reference(BaseReference):
    """
    A reference to a NineML user layer object previously defined or defined
    elsewhere.

    **Arguments**:
        *name*
            The name of a NineML object which already exists, or which is
            defined in a separate XML file.
        *document*
            A dictionary or :class:`Document` object containing the object
            being referred to, if the object already exists.
        *url*
            If the object is defined in a separate XML file, the URL
            of the file.

    """
    nineml_type = "Reference"

    @property
    def user_object(self):
        """The object being referred to."""
        return self._referred_to

    def clone(self, **kwargs):  # @UnusedVariable
        # Typically won't be called unless Reference is created and referenced
        # explicitly as the referenced object themselves is typically referred
        # to in the containing container.
        return copy(self)
# 
# 
# def resolve_reference(from_xml):
#     def resolving_from_xml(cls, element, document, **kwargs):  # @UnusedVariable @IgnorePep8
#         if element.tag in (ns + Reference.nineml_type for ns in ALL_NINEML):
#             reference = Reference.from_xml(element, document)
#             obj = reference.user_object
#         else:
#             obj = from_xml(cls, element, document)
#         return obj
#     return resolving_from_xml
# 
# 
# def write_reference(to_xml):
#     def unresolving_to_xml(self, document, as_ref=None, absolute_refs=False,
#                            prefer_refs=None, **kwargs):
#         # Determine whether to write the elemnt as a reference or not depending
#         # on whether it needs to be, as determined by `as_ref`, e.g. in the
#         # case of populations referenced from projections, or whether the user
#         # would prefer it to be, `prefer_refs`. If neither kwarg is set whether
#         # the element is written as a reference is determined by whether it
#         # has already been added to a document or not.
#         if as_ref is None:
#             if prefer_refs is None:
#                 # No preference is supplied so the element will be written as
#                 # a reference if it was loaded from a reference
#                 as_ref = self.document is not None
#             elif prefer_refs:
#                 # Write the element as a reference
#                 as_ref = True
#             else:
#                 # Write the element inline
#                 as_ref = False
#         # If the element is to be written as a reference and it is not in the
#         # current document add it
#         if as_ref and self.document is None:
#             try:
#                 obj = document[self.name]
#                 if obj != self:
#                     # Cannot write as a reference as an object of that name
#                     # already exists in the document
#                     as_ref = False
#             except NineMLNameError:
#                 # Add the object to the current document
#                 document.add(self, **kwargs)
#         if as_ref:
#             # If the object is already in the current document the url is None
#             if (self.document is None or
#                 self.document is document or
#                     self.document.url == document.url):
#                 url = None
#             # Use the full ref if the `absolute_refs` kwarg is provided
#             elif absolute_refs:
#                 url = self.document.url
#             # Otherwise use the relative path, which is recommended as it makes
#             # directories of 9ML documents transportable
#             else:
#                 url = os.path.relpath(self.document.url,
#                                       os.path.dirname(document.url))
#                 # Ensure the relative path starts with theh explicit
#                 # current directory '.'
#                 if not url.startswith('.'):
#                     url = './' + url
#             # Write the element as a reference
#             xml = Reference(self.name, document, url=url).to_xml(
#                 document, **kwargs)
#         else:
#             # Write the element inline. NB: This will effectively duplicate the
#             # object in the saved xml if it is referred to in multiple places.
#             # To avoid this from happening it is safer to avoid inline
#             # definitions by setting the `prefer_refs` kwarg.
#             xml = to_xml(self, document, absolute_refs=absolute_refs,
#                          prefer_refs=prefer_refs, **kwargs)
#         return xml
#     return unresolving_to_xml


import nineml  # @IgnorePep8
