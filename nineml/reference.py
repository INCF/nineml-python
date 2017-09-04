import os
from .base import AnnotatedNineMLObject
from nineml.exceptions import NineMLRuntimeError
from nineml.base import DocumentLevelObject


class BaseReference(AnnotatedNineMLObject):

    """
    Base class for references to model components that are defined in the
    abstraction layer.

    Parameters
    ----------
    target : BaseNineMLOjbect
        The target object. Not typically provided but allowed as a kwarg to
        allow the Cloner to properly clone references
    name : str
        Name of the target object in the given document
    document : Document | None
        The document in which the reference is located
    url : URL | None
        The URL of the document in which the target object is located. If None,
        the target object is assumed to be in the reference document
    """

    defining_attributes = ('url', '_target')
    child_attrs = {'target': None}

    def __init__(self, target=None, name=None, url=None, document=None):
        super(BaseReference, self).__init__()
        if target is not None:
            assert isinstance(target, DocumentLevelObject)
            self._target = target
            if name is not None or url is not None or document is not None:
                raise NineMLRuntimeError(
                    "'name', 'url' and 'document' kwargs cannot be used in "
                    "conjunction with 'target'")
        else:
            assert name is not None
            document_url = document.url if document is not None else None
            if url is not None and url != document_url:
                if url.startswith('.'):
                    if document_url is None:
                        raise NineMLRuntimeError(
                            "Must supply a document with a non-None URL that "
                            "is being referenced from if definition is a "
                            "relative URL string, '{}'".format(url))
                    relative_to = os.path.dirname(document.url)
                else:
                    relative_to = None
                if (relative_to is not None and
                    os.path.realpath(os.path.join(relative_to,
                                                  url)) == document_url):
                    remote_doc = document
                else:
                    remote_doc = nineml.read(url, relative_to=relative_to)
            else:
                remote_doc = document
            self._target = remote_doc[name]

    @property
    def name(self):
        return self._target.name

    @property
    def url(self):
        return self._target.url

    @property
    def target(self):
        return self._target

    @property
    def key(self):
        return (self._target.key +
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
        return (self._target == other._target and
                self.url == other.url and
                self.annotations_equal(other, **kwargs))

    def __hash__(self):
        return (hash(self.__class__) ^ hash(self._target.name) ^
                hash(self.url))

    def __repr__(self):
            return ('{}(name="{}"{})'
                    .format(self.__class__.__name__, self._target.name,
                            ' in "{}"'.format(self.url) if self.url else ''))

    def serialize_node(self, node, **options):  # @UnusedVariable
        name = self._target.name
        node.attr('name', name, **options)
        if self.url is not None and self.url != node.document.url:
            node.attr('url', self.url, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        name = node.attr('name', **options)
        url = node.attr('url', default=None, **options)
        return cls(name=name, document=node.document, url=url)

    def serialize_node_v1(self, node, **options):  # @UnusedVariable
        name = self._target.name
        node.body(name, **options)
        if self.url is not None and self.url != node.document.url:
            node.attr('url', self.url, **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):  # @UnusedVariable
        name = node.body(**options)
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

#     def clone(self, **kwargs):  # @UnusedVariable
#         # Typically won't be called unless Reference is created and referenced
#         # explicitly as the referenced object themselves is typically referred
#         # to in the containing container.
#         return copy(self)


import nineml  # @IgnorePep8
