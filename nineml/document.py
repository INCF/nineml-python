import os.path
from itertools import chain
from urllib import urlopen
import weakref
from copy import deepcopy
import time
from lxml import etree
import collections
from nineml.xml import (
    E, ALL_NINEML, extract_xmlns, NINEMLv1, get_element_maker)
from nineml.annotations import Annotations
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLXMLError)
from nineml.base import BaseNineMLObject, DocumentLevelObject
import contextlib
from nineml.utils import expect_single


class Document(dict, BaseNineMLObject):
    """
    Loads and stores all top-level elements in a NineML file (i.e. any element
    that is able to sit directly within <NineML>...</NineML> tags). All
    elements are stored initially but only converted to lib9ml objects on
    demand so it doesn't matter which order they appear in the NineML file.
    """

    defining_attributes = ('elements',)
    nineml_type = 'NineML'
    write_order = ['Population', 'Projection', 'Selection', 'Network',
                   'Dynamics', 'ConnectionRule', 'RandomDistribution',
                   'ComponentClass', 'Component',  # For v1.0
                   'DynamicsProperties', 'MultiDynamicsProperties',
                   'MultiCompartment', 'ConnectionRuleProperties',
                   'RandomDistributionProperties', 'Dimension', 'Unit']

    # A tuple to hold the unresolved elements
    _Unloaded = collections.namedtuple('_Unloaded', 'name xml cls kwargs')

    _loaded_docs = {}

    def __init__(self, *elements, **kwargs):
        BaseNineMLObject.__init__(self,
                                  annotations=kwargs.pop('annotations', None))
        url = kwargs.pop('url', None)
        if kwargs.pop('register_url', True):
            self._url = None  # Required for url setter
            self.url = url
        else:
            self._url = os.path.abspath(url)
        assert len(kwargs) == 0, ("Unrecognised kwargs '{}'"
                                  .format("', '".join(kwargs.iterkeys())))
        for element in elements:
            self.add(element)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []

    def add(self, element):
        if not isinstance(element, (DocumentLevelObject, self._Unloaded)):
            raise NineMLRuntimeError(
                "Could not add {} to document '{}' as it is not a 'document "
                "level NineML object' ('{}')"
                .format(element.nineml_type, self.url,
                        "', '".join(self.top_level_types)))
        if element.name in self:
            # Ignore if the element is already added (this can happend
            # implictly when writing other elements that refer to this element)
            if element is not self[element.name]:
                raise NineMLNameError(
                    "Could not add element '{}' as an element with that name "
                    "already exists in the document '{}'"
                    .format(element.name, self.url))
        else:
            if not isinstance(element, self._Unloaded):
                if element.document is None:
                    element._document = self  # Set its document to this one
                else:
                    raise NineMLNameError(
                        "Attempting to add the same object '{}' {} to '{}' "
                        "document '{}' when it is already in '{}'. Please "
                        "remove it from the original document first"
                        .format(element.name, element.nineml_type,
                                self.url, element.document.url))
            self[element.name] = element

    def remove(self, element, ignore_missing=False):
        if not isinstance(element, DocumentLevelObject):
            raise NineMLRuntimeError(
                "Could not remove {} from document as it is not a document "
                "level NineML object ('{}') ".format(element.nineml_type))
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

    def __eq__(self, other):
        # Ensure all objects are loaded
        self.values()
        other.values()
        # Use the parent dictionary class equality
        return (super(Document, self).__eq__(other) and
                self.url == other.url)

    def __ne__(self, other):
        return not self == other

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
            raise NineMLNameError(
                "'{}' was not found in the NineML document {} (elements in the"
                " document were '{}')."
                .format(name, self.url or '', "', '".join(self.iterkeys())))
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
        for v in super(Document, self).itervalues():
            if isinstance(v, self._Unloaded):
                v = self._load_elem_from_xml(v)
            yield v

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        for k, v in super(Document, self).iteritems():
            if isinstance(v, self._Unloaded):
                v = self._load_elem_from_xml(v)
            yield k, v

    def items(self):
        return list(self.iteritems())

    @property
    def components(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user.Component))  # @UndefinedVariable @IgnorePep8

    @property
    def componentclasses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.abstraction.ComponentClass))  # @UndefinedVariable @IgnorePep8

    @property
    def populations(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user.Population))  # @UndefinedVariable @IgnorePep8

    @property
    def projections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user.Projection))  # @UndefinedVariable @IgnorePep8

    @property
    def selections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user.Selection))  # @UndefinedVariable @IgnorePep8

    @property
    def network_structures(self):
        return chain(self.populations, self.projections, self.selections)

    @property
    def units(self):
        return (o for o in self.itervalues()
                if isinstance(nineml.units.Unit))  # @UndefinedVariable @IgnorePep8

    @property
    def dimensions(self):
        return (o for o in self.itervalues()
                if isinstance(nineml.units.Dimension))  # @UndefinedVariable @IgnorePep8

    def _load_elem_from_xml(self, unloaded):
        """
        Resolve an element from its XML description and store back in the
        element dictionary
        """
        if unloaded in self._loading:
            raise NineMLRuntimeError(
                "Circular reference detected in '{}(name={})' element. "
                "Resolution stack was:\n"
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
            self[unit.name] = unit
        for dimension in all_dimensions:
            if dimension.name in self:
                if dimension != self[dimension.name]:
                    raise NineMLRuntimeError(
                        "Name of dimension '{}' conflicts with existing object"
                        " of differring value or type '{}' and '{}'"
                        .format(dimension.name, dimension, self[unit.name]))
            self[dimension.name] = dimension
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

    def to_xml(self, E=E, **kwargs):  # @UnusedVariable
        self.standardize_units()
        return E(
            self.nineml_type,
            *[e.to_xml(self, as_ref=False)
              for e in self.sorted_elements()])

    @classmethod
    def from_xml(cls, element, url=None, register_url=True, **kwargs):
        xmlns = extract_xmlns(element.tag)
        if xmlns not in ALL_NINEML:
            raise NineMLXMLError(
                "Unrecognised XML namespace '{}', can be one of '{}'"
                .format(xmlns[1:-1],
                        "', '".join(ns[1:-1] for ns in ALL_NINEML)))
        if element.tag[len(xmlns):] != cls.nineml_type:
            raise NineMLXMLError("'{}' document does not have a NineML root "
                                 "('{}')".format(url, element.tag))
        # Initialise the document
        elements = []
        # Loop through child elements, determine the class needed to extract
        # them and add them to the dictionary
        annotations = None
        for child in element.getchildren():
            if isinstance(child, etree._Comment):
                continue
            if child.tag.startswith(xmlns):
                nineml_type = child.tag[len(xmlns):]
                if nineml_type == Annotations.nineml_type:
                    assert annotations is None, \
                        "Multiple annotations tags found"
                    annotations = Annotations.from_xml(child, **kwargs)
                    continue
                try:
                    # Note that all `DocumentLevelObjects` need to be imported
                    # into the root nineml package
                    child_cls = getattr(nineml, nineml_type)
                    if (not issubclass(child_cls, DocumentLevelObject) or
                            not hasattr(child_cls, 'from_xml')):
                        raise NineMLRuntimeError(
                            "'{}' element does not correspond to a recognised "
                            "document-level object".format(child_cls.__name__))
                except AttributeError:
                    # Check for v1 document-level objects
                    if (xmlns, nineml_type) == (NINEMLv1, 'ComponentClass'):
                        child_cls = get_component_class_type(child)
                    elif (xmlns, nineml_type) == (NINEMLv1, 'Component'):
                        child_cls = get_component_type(child, element, url)
                    else:
                        raise NineMLXMLError(
                            "Did not find matching NineML class for '{}' "
                            "element".format(nineml_type))
                if not issubclass(child_cls, DocumentLevelObject):
                    raise NineMLXMLError(
                        "'{}' is not a valid top-level NineML element"
                        .format(nineml_type))
            else:
                raise NotImplementedError(
                    "Cannot load '{}' element (extensions not implemented)"
                    .format(child.tag))
            # Units use 'symbol' as their unique identifier (from LEMS) all
            # other elements use 'name'
            try:
                try:
                    name = child.attrib['name']
                except KeyError:
                    name = child.attrib['symbol']
            except KeyError:
                raise NineMLXMLError(
                    "Missing 'name' (or 'symbol') attribute from document "
                    "level object '{}'".format(child))
            if name in elements:
                raise NineMLXMLError(
                    "Duplicate identifier '{ob1}:{name}'in NineML file '{url}'"
                    .format(name=name, ob1=elements[name].cls.nineml_type,
                            ob2=child_cls.nineml_type, url=url or ''))
            elements.append(cls._Unloaded(name, child, child_cls, kwargs))
        document = cls(*elements, url=url, annotations=annotations,
                       register_url=register_url)
        return document

    def duplicate(self):
        """
        Creates a duplicate of the current document with its url set to None to
        allow it to be written to a different file
        """
        new = deepcopy(self)
        new._url = None
        return new

    def write(self, url, version=2.0, **kwargs):
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
        # Update the modification time on the loaded doc
        self._register_url(self, url)

    @classmethod
    def load(cls, xml, url=None, register_url=True, **kwargs):
        """
        Loads the lib9ml object model from a root lxml.etree.Element. If the
        document has been previously loaded it is reused. To reload a document
        that has been changed on file, please delete any references to it first

        xml -- the 'NineML' etree.Element to load the object model
               from
        url -- specifies the url that the xml should be considered
               to have been read from in order to resolve relative
               references
        """
        if isinstance(xml, basestring):
            xml = etree.fromstring(xml)
            mod_time = None
        else:
            if url is None:
                mod_time = None
            else:
                mod_time = time.ctime(os.path.getmtime(url))
        doc = None
        if url is not None and register_url:
            # Check whether the document has already been loaded and is is
            # still in memory
            try:
                # Loaded docs are stored as weak refs to allow the document to
                # be released from memory by the garbarge collector
                doc_ref, saved_time = cls._loaded_docs[url]
                # NB: weakrefs to garbarge collected objs eval to None
                doc = doc_ref()
                if doc is not None and saved_time is not None:
                    if mod_time is None:
                        raise NineMLRuntimeError(
                            "Cannot reuse the '{}' url for two different XML "
                            "strings".format(url))
                    elif saved_time != mod_time:
                        raise NineMLRuntimeError(
                            "'{}' has been modified between reads. To reload "
                            "please remove all references to the original "
                            "version and permit it to be garbarge collected "
                            "(see https://docs.python.org/2/c-api/intro.html"
                            "#objects-types-and-reference-counts)".format(url))
            except KeyError:  # If the url hasn't been loaded before
                pass
        if doc is None:
            doc = Document.from_xml(xml, url=url, register_url=register_url,
                                    **kwargs)
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
            url = os.path.abspath(url)
            try:
                doc_ref, _ = self._loaded_docs[url]
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
            if self.url is None:
                self._register_url(self, url)
            else:
                url = os.path.abspath(url)
                # TODO: should validate URL properly
                if not isinstance(url, basestring):
                    raise NineMLRuntimeError(
                        "{} is not a valid URL")
                # Change the reference to the document in the loaded docs
                doc_and_time = self._loaded_docs.pop(self.url, None)
                if doc_and_time:
                    self._loaded_docs[url] = doc_and_time
            # Update the url
            self._url = url

    @classmethod
    def _register_url(cls, doc, url):
        try:
            mod_time = time.ctime(os.path.getmtime(url))
        except OSError:
            mod_time = None
        # Use weakref to avoid the registration from preventing GC
        cls._loaded_docs[url] = weakref.ref(doc), mod_time

    def find_mismatch(self, other):
        """
        A function used to display where two documents differ (typically used
        in unit test debugging)
        """
        result = 'Mismatch between documents:'
        for k, s in self.iteritems():
            if s != other[k]:
                result += s.find_mismatch(other[k])
        return result

    def as_network(self, name):
        return nineml.user.Network(
            name, populations=self.populations, projections=self.projections,
            selections=self.selections, document=self)

    def sorted_elements(self):
        """Sorts elements into a consistent order before write"""
        return sorted(
            self.elements,
            key=lambda e: (self.write_order.index(e.nineml_type), e.name))


def read(url, relative_to=None, force_reload=False, **kwargs):
    """
    Read a NineML file and parse its child elements

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    # Try to read
    doc = None
    if not force_reload:
        try:
            # Get the loaded document if it has been loaded previously and
            # still in memory
            doc = Document._loaded_docs[os.path.abspath(url)][0]()
        except KeyError:
            pass
    if doc is None:
        xml, url = read_xml(url, relative_to=relative_to)
        root = xml.getroot()
        doc = Document.load(root, url, **kwargs)
    return doc


def write(document, filename, **kwargs):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
    """
    # Encapsulate the NineML element in a document if it is not already
    if not isinstance(document, Document):
        document = Document(document)
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
                raise NineMLRuntimeError("Could not read 9ML URL '{}': \n{}"
                                         .format(url, e))
        else:
            xml = etree.parse(url)
    except etree.LxmlError, e:
        raise NineMLRuntimeError("Could not parse XML of 9ML file '{}': \n {}"
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
    url = definition.get('url')
    if url:
        doc_xml = read_xml(url, relative_to)
    for ref_elem in chain(doc_xml.findall(NINEMLv1 + 'ComponentClass'),
                          doc_xml.findall(NINEMLv1 + 'Component')):
        if ref_elem.attrib['name'] == definition.text:
            if ref_elem.tag == NINEMLv1 + 'ComponentClass':
                cc_cls = get_component_class_type(ref_elem)
                if cc_cls == nineml.Dynamics:
                    cls = nineml.user.component.DynamicsProperties
                elif cc_cls == nineml.ConnectionRule:
                    cls = nineml.user.component.ConnectionRuleProperties
                elif cc_cls == nineml.RandomDistribution:
                    cls = nineml.user.component.RandomDistributionProperties
                else:
                    assert False
            else:
                # Recurse through the prototype until we find the component
                # class at the bottom of it.
                cls = get_component_type(ref_elem, doc_xml, url)
            return cls
    assert False


import nineml
