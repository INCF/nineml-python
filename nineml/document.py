from itertools import chain
from nineml.base import clone_id, BaseNineMLVisitor
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError)
from nineml.base import AnnotatedNineMLObject, DocumentLevelObject
from logging import getLogger


logger = getLogger('lib9ml')


def write_order_key(nineml_obj):
    try:
        index = Document.write_order.index(nineml_obj.nineml_type)
    except ValueError:
        index = 100000
    return index, nineml_obj.name


class Document(AnnotatedNineMLObject, dict):
    """
    Loads and stores all top-level elements in a NineML file (i.e. any element
    that is able to sit directly within <NineML>...</NineML> tags). All
    elements are stored initially but only converted to lib9ml objects on
    demand so it doesn't matter which order they appear in the NineML file.

    Parameters
    ----------
    *args : list[DocumentLevelObject]
        Document level objects to be added to the object (after being cloned)

    Kwargs
    ------
    url : str
        The url assigned to the document
    annotations :
        Annotations to add to the document
    """

    defining_attributes = ('elements',)
    nineml_type = 'NineML'

    write_order = ('Network', 'Population', 'Projection', 'Selection',
                   'ComponentArray', 'EventConnectionGroup',
                   'AnalogConnectionGroup', 'Dynamics', 'ConnectionRule',
                   'RandomDistribution', 'DynamicsProperties',
                   'ConnectionRuleProperties', 'RandomDistributionProperties',
                   'Dimension', 'Unit')

    # Holds loaded documents to avoid reloading each time
    registry = {}

    def __init__(self, *nineml_objects, **kwargs):
        AnnotatedNineMLObject.__init__(
            self, annotations=kwargs.pop('annotations', None))
        self._url = kwargs.pop('url', None)
        self._unserializer = kwargs.pop('unserializer', None)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []
        memo = kwargs.pop('memo', {})
        for nineml_obj in nineml_objects:
            self.add(
                nineml_obj, memo=memo,
                clone_definitions=kwargs.pop('clone_definitions', 'local'),
                **kwargs)

    def __repr__(self):
        return "NineMLDocument(url='{}', {} elements)".format(
            str(self.url), len(self))

    def add(self, nineml_obj, clone=True, clone_definitions='local', **kwargs):
        """
        Adds a cloned version of the element to the document, setting the
        document reference (and the corresponding url) of clones to the
        document.

        Parameters
        ----------
        nineml_obj : DocumentLevelObject
            A document level object to add to the document
        clone : bool
            Whether to clone the element before adding it to the document
        clone_definitions : str
            Whether to clone definitions of user layer objects
        kwargs : dict
            Keyword arguments passed to the clone method
        """
        if not isinstance(nineml_obj, DocumentLevelObject):
            raise NineMLRuntimeError(
                "Cannot add {} element to document as it is not a \"document"
                "-level\" object".format(nineml_obj))
        if nineml_obj.name in self:
            # Ignore if the element is already added (this can happen
            # implictly when writing other elements that refer to this element)
            if nineml_obj is not self[nineml_obj.name]:
                if nineml_obj == self[nineml_obj.name]:
                    nineml_obj = self[nineml_obj.name]
                else:
                    raise NineMLNameError(
                        "Could not add '{}' as a different object with that "
                        "name already exists in the document '{}'"
                        .format(nineml_obj.name, self.url))
        elif nineml_obj.document is not None and not clone:
            raise NineMLRuntimeError(
                "Attempting to add the same object '{}' {} to document"
                " '{}' document when it is already in another "
                "document, '{}' and 'clone' kwarg is False"
                .format(nineml_obj.name, nineml_obj.nineml_type,
                        self.url, nineml_obj.document.url))
        else:
            if clone:
                nineml_obj = nineml_obj.clone(
                    clone_definitions=clone_definitions, **kwargs)
            AddToDocumentVisitor(self).visit(nineml_obj, **kwargs)
        return nineml_obj

    def remove(self, nineml_obj, ignore_missing=False):
        if not isinstance(nineml_obj, DocumentLevelObject):
            raise NineMLRuntimeError(
                "Could not remove {} from document as it is not a document "
                "level NineML object ('{}') ".format(nineml_obj.key,
                                                     nineml_obj.nineml_type))
        try:
            del self[nineml_obj.name]
        except KeyError:
            if not ignore_missing:
                raise NineMLNameError(
                    "Could not find '{}' element to remove from document '{}'"
                    .format(nineml_obj.name, self.url))
        assert nineml_obj.document is self
        nineml_obj._document = None

    def pop(self, name):
        element = self[name]
        self.remove(element)
        return element

    def __getitem__(self, name):
        """
        Returns the element referenced by the given name
        """
        if name is None:
            # FIXME: This is a hack that should be removed
            # This simplifies code in a few places where an optional
            # attribute refers to a name of an object which
            # should be resolved if present but be set to None if not.
            return None
        try:
            nineml_obj = super(Document, self).__getitem__(name)
        except KeyError:
            if self._unserializer is not None:
                nineml_obj = self._unserializer.load_element(name)
            else:
                raise NineMLNameError(
                    "'{}' was not found in the NineML document {} (elements in"
                    " the document were '{}').".format(
                        name, self.url or '', "', '".join(self.iterkeys())))
        return nineml_obj

    def __setitem__(self, name, nineml_obj):
        if nineml_obj.name != name:
            raise NineMLRuntimeError(
                "Cannot set {} to a different name ('{}') within document "
                "({})".format(nineml_obj, name, self.url))
        self.add(nineml_obj)

    def __contains__(self, name):
        if super(Document, self).__contains__(name):
            return True
        elif self._unserializer is None:
            return False
        else:
            return name in self._unserializer.keys()

    @property
    def elements(self):
        return self.itervalues()

    @property
    def nineml_types(self):
        return (e.name for e in self.elements)

    def itervalues(self):
        self._load_all()
        return dict.itervalues(self)

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        self._load_all()
        return dict.iteritems(self)

    def items(self):
        return list(self.iteritems())

    def iterkeys(self):
        return (self._unserializer.iterkeys()
                if self._unserializer is not None else
                super(Document, self).iterkeys())

    def keys(self):
        return list(self.iterkeys())

    def _load_all(self):
        """
        Ensure all elements are loaded before iterating, as additional
        elements may be added to the document during the load process
        """
        for name in dict.keys(self):
            self[name]

    def clone(self, memo=None, refs=None, **kwargs):
        """
        Creates a duplicate of the current document with its url set to None to
        allow it to be written to a different file

        Parameters
        ----------
        refs : list[BaseReference]
            A list of all the references within the clone that may need to be
            updated once all objects are cloned
        """
        if memo is None:
            memo = {}
        if refs is None:
            refs = []
        try:
            clone = memo[clone_id(self)]
        except KeyError:
            clone = Document(*self.values(), memo=memo, refs=refs,
                             clone=True, **kwargs)
            memo[clone_id(self)] = clone
            # Updated any cloned references to point to cloned objects
            for ref in refs:
                if id(ref._referred_to) in memo:
                    ref._referred_to = memo[id(ref._referred_to)]
        return clone

    def find_mismatch(self, other):
        """
        A function used to display where two documents differ (typically used
        in unit test debugging)
        """
        result = 'Mismatch between documents: '
        if self.nineml_type != other.nineml_type:
            result += ("mismatch in nineml_type, self:'{}' and other:'{}'"
                       .format(self.nineml_type, other.nineml_type))
        else:
            for k, s in self.iteritems():
                if k not in other:
                    result += ("\n    {}(name='{}') is not present in second "
                               "document".format(type(s).__name__, k))
                elif s != other[k]:
                    result += ("\n    {}(name='{}'):".format(type(s).__name__,
                                                             k) +
                               s.find_mismatch(other[k], '        '))
            for k, o in other.iteritems():
                if k not in self:
                    result += ("\n    {}(name='{}') is not present in first "
                               "document".format(type(o).__name__, k))
        return result

    def as_network(self, name):
        # Return Document as a Network object
        return nineml.user.Network(
            name, populations=self.populations, projections=self.projections,
            selections=self.selections)

    def serialize_node(self, node, **options):
        node.children(
            sorted(self.elements, key=write_order_key), reference=False,
            **options)

    @property
    def url(self):
        return self._url


class AddToDocumentVisitor(BaseNineMLVisitor):
    """
    Traverses any 9ML object and adds any "unbound" objects to the document (or
    optionally clones of bound), i.e. objects that currently don't belong to
    any other document

    Parameters
    ----------
    document : Document
        Document to add the unbound elements to
    add_bound : bool
        Whether to add the object even if it belongs to another document
        (but not this one). Useful for combining all referenced objects
        into a single document.
    """

    def __init__(self, document, add_bound=False, **kwargs):  # @UnusedVariable
        super(AddToDocumentVisitor, self).__init__()
        self.document = document
        self.add_bound = add_bound

    def action(self, obj, **kwargs):  # @UnusedVariable
        """
        Adds the object to the document if is a DocumentLevelObject and it
        doesn't already belong to a document (or regardless if 'add_bound' is
        True)

        Parameters
        ----------
        obj : BaseNineMLObject
            The object to add the document if is DocumentLevelObject
        """
        if (isinstance(obj, DocumentLevelObject) and (obj.document is None or
                                                      self.add_bound)):
            if obj.name in dict.iterkeys(self.document):
                doc_obj = self.document[obj.name]
                orig_doc = obj._document
                try:
                    # Set document of object to current document before
                    # checking for equality with document already in document
                    obj._document = self.document
                    if obj == doc_obj:
                        if obj is not doc_obj and self.context is not None:
                            self.context.replace(obj, doc_obj)
                    else:
                        raise NineMLRuntimeError(
                            "Cannot add {} '{}' to the document {} as it "
                            "clashes with existing (potentially nested) {}."
                            .format(obj.nineml_type, obj.name,
                                    self.document.url,
                                    self.document[obj.name].nineml_type))
                finally:
                    obj._document = orig_doc  # Reset doc to previous state
                obj = doc_obj
            else:
                dict.__setitem__(self.document, obj.name, obj)
                obj._document = self.document
        return obj

    def post_action(self, *args, **kwargs):
        pass

    def final(self, obj, **kwargs):
        pass

import nineml  # @IgnorePep8
