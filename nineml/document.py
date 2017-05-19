import os.path
import re
from itertools import chain
import weakref
import time
from nineml.base import clone_id, AddNestedObjectsToDocumentVisitor
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLIOError,
    NineMLUpdatedFileException)
from nineml.base import AnnotatedNineMLObject, DocumentLevelObject
from logging import getLogger
from nineml.serialization import read


logger = getLogger('lib9ml')

url_re = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|'
    '[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

file_path_re = re.compile(r'^(\.){0,2}\/+([\w\._\-]\/+)*[\w\._\-]')


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
    """

    defining_attributes = ('elements',)
    nineml_type = 'NineML'

    # Holds loaded documents to avoid reloading each time
    registry = {}

    def __init__(self, *elements, **kwargs):
        AnnotatedNineMLObject.__init__(
            self, annotations=kwargs.pop('annotations', None))
        self._url = self._standardise_url(kwargs.pop('url', None))
        self._unserializer = kwargs.pop('unserializer', None)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []
        memo = kwargs.pop('memo', {})
        for element in elements:
            self.add(
                element, memo=memo,
                clone_definitions=kwargs.pop('clone_definitions', 'local'),
                **kwargs)

    def __repr__(self):
        return "NineMLDocument(url='{}', {} elements)".format(
            str(self.url), len(self))

    def add(self, element, clone=True, clone_definitions='local', **kwargs):
        """
        Adds a cloned version of the element to the document, setting the
        document reference (and the corresponding url) of clones to the
        document.

        Parameters
        ----------
        element : DocumentLevelObject
            A document level object to add to the document
        clone : bool
            Whether to clone the element before adding it to the document
        kwargs : dict
            Keyword arguments passed to the clone method
        """
        if not isinstance(element, (DocumentLevelObject, self._Unloaded)):
            raise NineMLRuntimeError(
                "Could not add {} to document '{}' as it is not a 'document "
                "level NineML object'"
                .format(element.nineml_type, self.url))
        if element.name in self:
            # Ignore if the element is already added (this can happen
            # implictly when writing other elements that refer to this element)
            if element is not self[element.name]:
                if element == self[element.name]:
                    element = self[element.name]
                else:
                    raise NineMLNameError(
                        "Could not add element '{}' as an element with that "
                        "name already exists in the document '{}'"
                        .format(element.name, self.url))
        else:
            if clone:
                element = element.clone(
                    clone_definitions=clone_definitions, **kwargs)
            elif element.document is not None:
                raise NineMLRuntimeError(
                    "Attempting to add the same object '{}' {} to document"
                    " '{}' document when it is already in another "
                    "document, '{}'. Please remove it from the original "
                    "document first or use the 'clone' keyword to add a "
                    "clone of the element instead"
                    .format(element.name, element.nineml_type,
                            self.url, element.document.url))
            element._document = self  # Set its document to this one
            # Add any nested objects that don't already belong
            # to another document
            AddNestedObjectsToDocumentVisitor(self).visit(element,
                                                          **kwargs)
            self[element.name] = element
        return element

    def remove(self, element, ignore_missing=False):
        if not isinstance(element, DocumentLevelObject):
            raise NineMLRuntimeError(
                "Could not remove {} from document as it is not a document "
                "level NineML object ('{}') ".format(element.key,
                                                     element.nineml_type))
        try:
            del self[element.name]
        except KeyError:
            if not ignore_missing:
                raise NineMLNameError(
                    "Could not find '{}' element to remove from document '{}'"
                    .format(element.name, self.url))
        assert element.document is self
        element._document = None

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
            elem = super(Document, self).__getitem__(name)
        except KeyError:
            if self._unserializer is not None:
                elem = self._unserializer.load_element(name)
            else:
                raise NineMLNameError(
                    "'{}' was not found in the NineML document {} (elements in"
                    " the document were '{}').".format(
                        name, self.url or '', "', '".join(self.iterkeys())))
        return elem

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
        self._load_all()
        return dict.iterkeys(self)

    def keys(self):
        return list(self.iterkeys())

    def _load_all(self):
        """
        Ensure all elements are loaded before iterating, as additional
        elements may be added to the document during the load process
        """
        for name in dict.keys(self):
            self[name]

    @property
    def components(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user.Component))  # @UndefinedVariable @IgnorePep8

    @property
    def componentclasses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.abstraction.ComponentClass))  # @UndefinedVariable @IgnorePep8

    @property
    def networks(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.Network))  # @UndefinedVariable @IgnorePep8

    @property
    def populations(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.Population))  # @UndefinedVariable @IgnorePep8

    @property
    def projections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.Projection))  # @UndefinedVariable @IgnorePep8

    @property
    def selections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.Selection))  # @UndefinedVariable @IgnorePep8

    @property
    def network_structures(self):
        return chain(self.populations, self.projections, self.selections)

    @property
    def component_arrays(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.ComponentArray))  # @UndefinedVariable @IgnorePep8

    @property
    def event_connection_groups(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.EventConnectionGroup))  # @UndefinedVariable @IgnorePep8

    @property
    def analog_connection_groups(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.AnalogConnectionGroup))  # @UndefinedVariable @IgnorePep8

    @property
    def dynamicses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.Dynamics))  # @UndefinedVariable @IgnorePep8

    @property
    def multi_dynamicses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.MultiDynamics))  # @UndefinedVariable @IgnorePep8

    @property
    def connection_rules(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.ConnectionRule))  # @UndefinedVariable @IgnorePep8

    @property
    def random_distributions(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.RandomDistribution))  # @UndefinedVariable @IgnorePep8

    @property
    def dynamics_propertieses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.DynamicsProperties))  # @UndefinedVariable @IgnorePep8

    @property
    def multi_dynamics_propertieses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.MultiDynamicsProperties))  # @UndefinedVariable @IgnorePep8

    @property
    def connection_rule_propertieses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.ConnectionRuleProperties))  # @UndefinedVariable @IgnorePep8

    @property
    def random_distribution_propertieses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.RandomDistributionProperties))  # @UndefinedVariable @IgnorePep8

    @property
    def units(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.Unit))  # @UndefinedVariable @IgnorePep8

    @property
    def dimensions(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.Dimension))  # @UndefinedVariable @IgnorePep8

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

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        if url != self.url:
            if url is None:
                raise NineMLRuntimeError(
                    "Cannot reset a documents url to None once it has been set"
                    "('{}') please duplicate the document instead"
                    .format(self.url))
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
            self._loaded_docs[url] = weakref.ref(self)
            # Update the url
            self._url = url

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
                    result = "{} is not present in other document".format(k)
                elif s != other[k]:
                    result += ('\n    {}({}):'.format(type(s).__name__, k) +
                               s.find_mismatch(other[k], '        '))
        return result

    def as_network(self, name):
        # Return Document as a Network object
        return nineml.user.Network(
            name, populations=self.populations, projections=self.projections,
            selections=self.selections, document=self)

    def serialize_node(self, node, **options):
        node.children(self.networks, reference=False, **options)
        node.children(self.populations, reference=False, **options)
        node.children(self.projections, reference=False, **options)
        node.children(self.selections, reference=False, **options)
        node.children(self.component_arrays, reference=False, **options)
        node.children(self.event_connection_groups, reference=False, **options)
        node.children(self.analog_connection_groups, reference=False,
                      **options)
        node.children(self.dynamicses, reference=False, **options)
        node.children(self.connection_rules, reference=False, **options)
        node.children(self.random_distributions, reference=False, **options)
        node.children(self.dynamics_propertieses, reference=False, **options)
        node.children(self.connection_rule_propertieses, reference=False,
                      **options)
        node.children(self.random_distribution_propertieses, reference=False,
                      **options)
        node.children(self.dimensions, reference=False, **options)
        node.children(self.units, reference=False, **options)

    @classmethod
    def load(cls, url, relative_to=None, reload=False):  # @ReservedAssignment
        if not isinstance(url, basestring):
            raise NineMLIOError(
                "{} is not a valid URL (it is not even a string)"
                .format(url))
        if file_path_re.match(url) is not None:
            if url.startswith('.'):
                if relative_to is None:
                    raise NineMLIOError(
                        "'relative_to' kwarg must be provided when using "
                        "relative paths (i.e. paths starting with '.'), "
                        "'{}'".format(url))
                url = os.path.abspath(os.path.join(relative_to, url))
                mtime = time.ctime(os.path.getmtime(url))
        elif url_re.match(url) is not None:
            mtime = None  # Cannot load mtime of a general URL
        else:
            raise NineMLIOError(
                "{} is not a valid URL or file path")
        if reload:
            cls.registry.pop(url, None)
        try:
            doc, loaded_mtime = cls.registry[url]
            if loaded_mtime != mtime:
                raise NineMLUpdatedFileException()
        except (KeyError, NineMLUpdatedFileException):
            doc = read(url)
            cls.registry[url] = doc, mtime
        return doc

import nineml  # @IgnorePep8
