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


import nineml  # @IgnorePep8
