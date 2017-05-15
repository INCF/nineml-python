import os.path
import re
from itertools import chain
from urllib import urlopen
import weakref
from lxml import etree
import collections
from nineml.base import clone_id, AddNestedObjectsToDocumentVisitor
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLXMLError, NineMLXMLTagError)
from nineml.base import AnnotatedNineMLObject, DocumentLevelObject
import contextlib
from nineml.utils import expect_single
from logging import getLogger


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

    # A tuple to hold the unresolved elements
    _Unloaded = collections.namedtuple('_Unloaded', 'name xml cls kwargs')

    _loaded_docs = {}

    def __init__(self, *elements, **kwargs):
        AnnotatedNineMLObject.__init__(
            self, annotations=kwargs.pop('annotations', None))
        self._url = self._standardise_url(kwargs.pop('url', None))
        self._unserializer = kwargs.pop('unserializer', None)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []
        self._added_in_write = None
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
            if not isinstance(element, self._Unloaded):
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
        if self._added_in_write is not None:
            self._added_in_write.append(element)
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
        # Load (lazily) the element from the xml description
        if isinstance(elem, self._Unloaded):
            elem = self._load_elem_from_xml(elem)
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

    def _load_elem_from_xml(self, unloaded):
        """
        Resolve an element from its XML description and store back in the
        element dictionary
        """
        if unloaded in self._loading:
            raise NineMLRuntimeError(
                "Circular reference detected in '{}(name={})' element. "
                "Resolution stack was:\n{}"
                .format(unloaded.cls.__name__, unloaded.name,
                        "\n".join('{}(name={})'.format(u.cls.__name__, u.name)
                                  for u in self._loading)))
        # Keep track of the document-level elements that are in the process of
        # being loaded to catch circular references
        self._loading.append(unloaded)
        elem = unloaded.cls.from_xml(unloaded.xml, self, **unloaded.kwargs)
        # Remove current element from "loading" stack as it has been loaded
        assert self._loading[-1] is unloaded
        self._loading.pop()
        assert isinstance(unloaded.name, basestring)
        self[unloaded.name] = elem
        return elem

    def standardize_units(self):
        """
        Standardized the units into a single set (no duplicates). Used to avoid
        naming conflicts when writing to file.
        """
        # Get the set of all units and dimensions that are used in the document
        # Note that Dimension & Unit objects are equal even if they have
        # different names so when this set is traversed the dimension/unit will
        # be substituted for the first equivalent dimension/unit.
        all_units = set(chain(*[o.all_units for o in self.itervalues()]))
        all_dimensions = set(chain(
            [u.dimension for u in all_units],
            *[o.all_dimensions for o in self.itervalues()]))
        # Delete unused units from the document
        for k, o in self.items():
            if ((isinstance(o, nineml.Unit) and o not in all_units) or
                (isinstance(o, nineml.Dimension) and
                 o not in all_dimensions)):
                del self[k]
        # Add missing units and dimensions to the document
        for unit in all_units:
            if unit.name in self:
                if unit != self[unit.name]:
                    raise NineMLRuntimeError(
                        "Name of unit '{}' conflicts with existing object of "
                        "differring value or type '{}' and '{}'"
                        .format(unit.name, unit, self[unit.name]))
            else:
                self[unit.name] = unit
                if self._added_in_write is not None:
                    self._added_in_write.append(unit)
        for dimension in all_dimensions:
            if dimension.name in self:
                if dimension != self[dimension.name]:
                    raise NineMLRuntimeError(
                        "Name of dimension '{}' conflicts with existing object"
                        " of differring value or type '{}' and '{}'"
                        .format(dimension.name, dimension,
                                self[dimension.name]))
            else:
                self[dimension.name] = dimension
                if self._added_in_write is not None:
                    self._added_in_write.append(dimension)
        # Replace units and dimensions with those in the superset
        for obj in self.itervalues():
            for a in obj.attributes_with_dimension:
                try:
                    std_dim = next(d for d in all_dimensions
                                   if d == a.dimension)
                except StopIteration:
                    assert False, \
                        ("Did not find matching dimension in supposed superset"
                         " of dimensions")
                a.set_dimension(std_dim)
            for a in obj.attributes_with_units:
                try:
                    std_units = next(u for u in all_units
                                     if u == a.units)
                except StopIteration:
                    assert False, \
                        ("Did not find matching unit in supposed superset"
                         " of units")
                a.set_units(std_units)

    @classmethod
    def _get_class_from_type(cls, nineml_type):
        # Note that all `DocumentLevelObjects` need to be imported
        # into the root nineml package
        try:
            child_cls = getattr(nineml, nineml_type)
            if (not issubclass(child_cls, DocumentLevelObject) or
                    not hasattr(child_cls, 'from_xml')):
                raise NineMLRuntimeError(
                    "'{}' element does not correspond to a recognised "
                    "document-level object".format(child_cls.__name__))
        except AttributeError:
            raise NineMLXMLTagError
        return child_cls

    @classmethod
    def _get_class_from_v1(cls, nineml_type, xmlns, child, element, url):
        # Check for v1 document-level objects
        if (xmlns, nineml_type) == (NINEMLv1, 'ComponentClass'):
            child_cls = get_component_class_type(child)
        elif (xmlns, nineml_type) == (NINEMLv1, 'Component'):
            relative_to = (os.path.dirname(url)
                           if url is not None else None)
            child_cls = get_component_type(child, element,
                                           relative_to)
        else:
            raise NineMLXMLTagError(
                "Did not find matching NineML class for '{}' " "element"
                .format(nineml_type))
        return child_cls

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

    def write(self, url, version=XML_VERSION, **kwargs):
        if self.url is None:
            self.url = url  # Required so relative urls can be generated
        elif self.url != url:
            raise NineMLRuntimeError(
                "Cannot write the same Document object to two different "
                "locations '{}' and '{}'. Please either explicitly change "
                "its `url` property or create a duplicate using the "
                "`duplicate` method before attempting to write it to the new "
                "location".format(self.url, url))
        doc_xml = self.to_xml(E=get_element_maker(version), **kwargs)
        write_xml(doc_xml, url)

    @classmethod
    def load(cls, xml, url=None, register_url=True, force_reload=False,
             **kwargs):
        """
        Loads the lib9ml object model from a root lxml.etree.Element. If the
        document has been previously loaded it is reused. To reload a document
        that has been changed on file, please delete any references to it first

        Parameters
        ----------
        xml : etree.Element
            The 'NineML' etree.Element to load the object model from
        url : str
            Specifies the url that the xml should be considered
            to have been read from in order to resolve relative
            references
        register_url : bool
            Whether to cache this loaded xml in the class dictionary
        force_reload : bool
            Whether to ignore existing entry in cache and force a reload of the
            xml from file
        """
        if isinstance(xml, basestring):
            xml = etree.fromstring(xml)
        url = cls._standardise_url(url)
        doc = cls.from_xml(xml, url=url, **kwargs)
        if force_reload:
            if url in cls._loaded_docs:
                logger.warning("Reloading '{}' URL, old references to this URL"
                               " should not be rewritten to file"
                               .format(url))
                del cls._loaded_docs[url]
        if register_url:
            if url is not None:
                # Check whether the document has already been loaded and is is
                # still in memory
                try:
                    # Loaded docs are stored as weak refs to allow the document
                    # to be released from memory by the garbarge collector
                    loaded_doc_ref = cls._loaded_docs[url]
                except KeyError:  # If the url hasn't been loaded before
                    loaded_doc_ref = None
                if loaded_doc_ref is not None:
                    # NB: weakrefs to garbarge collected objs eval to None
                    loaded_doc = loaded_doc_ref()
                    if loaded_doc is not None and loaded_doc != doc:
                        raise NineMLRuntimeError(
                            "Cannot reuse the '{}' url for two different "
                            "documents (NB: the file may have been modified "
                            "externally between reads). To reload please "
                            "remove all references to the original version "
                            "and permit it to be garbarge collected "
                            "(see https://docs.python.org/2/c-api/intro.html"
                            "#objects-types-and-reference-counts): {}".format(
                                url, doc.find_mismatch(loaded_doc)))
            doc.url = url
        else:
            doc._url = url  # Bypass registering the URL, used in testing
        return doc

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
        # Ensure that all elements are loaded
        loaded_elems = self.values()  # @UnusedVariable
        # Return Document as a Network object
        return nineml.user.Network(
            name, populations=self.populations, projections=self.projections,
            selections=self.selections, document=self)

    @classmethod
    def _standardise_url(cls, url):
        if url is not None:
            if isinstance(url, basestring):
                if file_path_re.match(url) is not None:
                    if url.startswith('.'):
                        url = os.path.abspath(url)
                elif url_re.match(url) is None:
                    raise NineMLRuntimeError(
                        "{} is not a valid URL or file path")
            else:
                raise NineMLRuntimeError(
                    "{} is not a valid URL (it is not even a string)"
                    .format(url))
        return url

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


def write(document, filename, **kwargs):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
    """
    # Encapsulate the NineML element in a document if it is not already
    if not isinstance(document, Document):
        document = Document(document, **kwargs)
    document.write(filename, **kwargs)


def read_xml(url, relative_to):
    if url.startswith('.') and relative_to:
        url = os.path.abspath(os.path.join(relative_to, url))
    try:
        if not isinstance(url, file):
            try:
                with contextlib.closing(urlopen(url)) as f:
                    xml = etree.parse(f)
            except IOError, e:
                raise NineMLXMLError("Could not read 9ML URL '{}': \n{}"
                                     .format(url, e))
        else:
            xml = etree.parse(url)
    except etree.LxmlError, e:
        raise NineMLXMLError("Could not parse XML of 9ML file '{}': \n {}"
                             .format(url, e))
    return xml, url


def write_xml(xml, filename):
    with open(filename, 'w') as f:
        etree.ElementTree(xml).write(f, encoding="UTF-8",
                                     pretty_print=True,
                                     xml_declaration=True)


def get_component_class_type(elem):
    if elem.findall(NINEMLv1 + 'Dynamics'):
        cls = nineml.Dynamics
    elif elem.findall(NINEMLv1 + 'ConnectionRule'):
        cls = nineml.ConnectionRule
    elif elem.findall(NINEMLv1 + 'RandomDistribution'):
        cls = nineml.RandomDistribution
    else:
        raise NineMLXMLError(
            "No type defining block in ComponentClass")
    return cls


def get_component_type(comp_xml, doc_xml, relative_to):
    definition = expect_single(chain(
        comp_xml.findall(NINEMLv1 + 'Definition'),
        comp_xml.findall(NINEMLv1 + 'Prototype')))
    name = definition.text
    url = definition.get('url', None)
    if url:
        doc = read(url, relative_to)
        cc_cls = doc[name].__class__
    else:
        cc_cls = None
        for ref_elem in chain(doc_xml.findall(NINEMLv1 + 'ComponentClass'),
                              doc_xml.findall(NINEMLv1 + 'Component')):
            if ref_elem.attrib['name'] == name:
                if ref_elem.tag == NINEMLv1 + 'ComponentClass':
                    cc_cls = get_component_class_type(ref_elem)
                    break
                elif ref_elem.tag == NINEMLv1 + 'Component':
                    # Recurse through the prototype until we find the component
                    # class at the bottom of it.
                    return get_component_type(ref_elem, doc_xml, url)
                else:
                    raise NineMLXMLError(
                        "'{}' refers to a '{}' element not a ComponentClass or"
                        " Component element".format(name, ref_elem.tag))
        if cc_cls is None:
            raise NineMLXMLError(
                "Did not find component or component class in '{}' tags"
                .format("', '".join(c.tag for c in doc_xml.getchildren())))
    cls = None
    while cls is None:
        if cc_cls == nineml.Dynamics:
            cls = nineml.user.dynamics.DynamicsProperties
        elif cc_cls == nineml.ConnectionRule:
            cls = (nineml.user.connectionrule.
                   ConnectionRuleProperties)
        elif cc_cls == nineml.RandomDistribution:
            cls = (nineml.user.randomdistribution.
                   RandomDistributionProperties)
        elif issubclass(cc_cls, nineml.user.Component):
            cls = cc_cls
        else:
            assert False, ("Unrecognised component class type '{}"
                           .format(cc_cls))
    return cls


import nineml  # @IgnorePep8
