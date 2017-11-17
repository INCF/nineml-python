from nineml.visitors.base import BaseVisitorWithContext
from nineml.visitors.equality import MismatchFinder
from nineml.exceptions import (
    NineMLUsageError, NineMLNameError)
from nineml.base import AnnotatedNineMLObject, DocumentLevelObject
from logging import getLogger
from nineml.visitors import Cloner


logger = getLogger('NineML')


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
    elements are stored initially but only converted to NineML Python objects
    on demand so it doesn't matter which order they appear in the NineML file.

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

    nineml_type = 'NineML'

    # Defines a consistent order that the different document-level types are
    # written to file.
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
        cloner = kwargs.pop('cloner', Cloner(document=self, **kwargs))
        for nineml_obj in nineml_objects:
            self.add(nineml_obj, cloner=cloner, **kwargs)

    def __repr__(self):
        return "NineMLDocument(url='{}', {} elements)".format(
            str(self.url), len(self))

    def add(self, nineml_obj, clone=True, cloner=None, **kwargs):
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
            raise NineMLUsageError(
                "Cannot add {} element to document as it is not a \"document"
                "-level\" object".format(nineml_obj))
        if nineml_obj.name in self:
            # Ignore if the element is already added (this can happen
            # implictly when writing other elements that refer to this element)
            if nineml_obj is not self[nineml_obj.name]:
                if nineml_obj == self[nineml_obj.name]:
                    nineml_obj = self[nineml_obj.name]
                else:
                    nineml_obj.find_mismatch(self[nineml_obj.name])
                    raise NineMLNameError(
                        "Could not add '{}' as a different object with that "
                        "name already exists in the document '{}':\n{}"
                        .format(nineml_obj.name, self.url,
                                nineml_obj.find_mismatch(
                                    self[nineml_obj.name])))
        elif nineml_obj.document is not None and not clone:
            raise NineMLUsageError(
                "Attempting to add the same object '{}' {} to document"
                " '{}' document when it is already in another "
                "document, '{}' and 'clone' kwarg is False"
                .format(nineml_obj.name, nineml_obj.nineml_type,
                        self.url, nineml_obj.document.url))
        else:
            if clone:
                if cloner is None:
                    cloner = Cloner(**kwargs)
                nineml_obj = cloner.clone(nineml_obj, **kwargs)
            AddToDocumentVisitor(self).visit(nineml_obj, **kwargs)
        return nineml_obj

    def remove(self, nineml_obj, ignore_missing=False):
        if not isinstance(nineml_obj, DocumentLevelObject):
            raise NineMLUsageError(
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
                        name, self.url or '', "', '".join(iter(self.keys()))))
        return nineml_obj

    def __setitem__(self, name, nineml_obj):
        if nineml_obj.name != name:
            raise NineMLUsageError(
                "Cannot set {} to a different name ('{}') within document "
                "({})".format(nineml_obj, name, self.url))
        self.add(nineml_obj)

    def __contains__(self, name):
        if super(Document, self).__contains__(name):
            return True
        elif self._unserializer is None:
            return False
        else:
            return name in list(self._unserializer.keys())

    @property
    def elements(self):
        return iter(self.values())

    @property
    def nineml_types(self):
        return (e.name for e in self.elements)

    def values(self):
        self._load_all()
        return dict.values(self)

    def items(self):
        self._load_all()
        return dict.items(self)

    def keys(self):
        return (iter(self._unserializer.keys())
                if self._unserializer is not None else
                iter(dict.keys(self)))

    def _load_all(self):
        """
        Ensure all elements are loaded before iterating, as additional
        elements may be added to the document during the load process
        """
        for name in dict.keys(self):
            self[name]

    def clone(self, cloner=None, **kwargs):
        """
        Creates a duplicate of the current document with its url set to None to
        allow it to be written to a different file

        Parameters
        ----------
        refs : list[BaseReference]
            A list of all the references within the clone that may need to be
            updated once all objects are cloned
        """
        if cloner is None:
            cloner = Cloner(**kwargs)
        return Document(*list(self.values()), clone=True, cloner=cloner,
                        **kwargs)

    def find_mismatch(self, other, **kwargs):
        finder = MismatchFinder(**kwargs)
        s_names = sorted(self.keys())
        o_names = sorted(other.keys())
        if s_names != o_names:
            return ("[] - element names: {} | {}"
                    .format(s_names, o_names))
        mismatch = ''
        for name in s_names:
            mismatch += finder.find(self[name], other[name], **kwargs)
        return mismatch

    def as_network(self, name):
        populations = []
        projections = []
        selections = []
        for elem in self.elements:
            if isinstance(elem, nineml.Population):
                populations.append(elem)
            elif isinstance(elem, nineml.Projection):
                projections.append(elem)
            elif isinstance(elem, nineml.Selection):
                selections.append(elem)
        # Return Document as a Network object
        return nineml.user.Network(
            name, populations=populations, projections=projections,
            selections=selections)

    def serialize_node(self, node, **options):
        node.children(
            sorted(self.elements, key=write_order_key), reference=False,
            **options)

    @property
    def url(self):
        return self._url


class AddToDocumentVisitor(BaseVisitorWithContext):
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
        if (isinstance(obj, DocumentLevelObject) and (
                self.add_bound or obj.document is None)):
            # Need to use dictionary keys method instead of document one
            # to be able to add objects that are being lazily added by the
            # unserializer whos keys appear in self.document.keys() (but not
            # dict.keys(self.document)).
            if obj.name in dict.keys(self.document):
                doc_obj = self.document[obj.name]
                if obj is doc_obj:
                    return obj  # Object is already in document
                if obj.equals(doc_obj, check_urls=False):
                    # If the object is nested in another object, replace
                    # it in the nesting object with the equivalent object in
                    # the document
                    if self.context is not None:
                        if self.context.attr_name is not None:
                            # If object is a child of the nesting object
                            setattr(self.context.parent,
                                    '_' + self.context.attr_name, doc_obj)
                        elif self.context.dct is not None:
                            # If the object is one of a set of children in the
                            # nesting container object
                            del self.context.dct[obj.name]
                            self.context.dct[doc_obj.name] = doc_obj
                else:
                    raise NineMLUsageError(
                        "Cannot add {} '{}' to the document {} as it "
                        "clashes with existing (potentially nested) {}."
                        .format(obj.nineml_type, obj.name,
                                self.document.url,
                                self.document[obj.name].nineml_type))
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
