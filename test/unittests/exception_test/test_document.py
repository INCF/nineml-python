import unittest
from nineml.document import (Document)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLXMLError, NineMLNameError, NineMLRuntimeError)


class TestDocumentExceptions(unittest.TestCase):

    def test_add_ninemlruntimeerror(self):
        """
        line #: 66
        message: Could not add {} to document '{}' as it is not a 'document level NineML object' ('{}')

        context:
        --------
    def add(self, element):
        if not isinstance(element, (DocumentLevelObject, self._Unloaded)):
        """

        document = next(instances_of_all_types['Document'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document.add,
            element=None)

    def test_add_ninemlnameerror(self):
        """
        line #: 75
        message: Could not add element '{}' as an element with that name already exists in the document '{}'

        context:
        --------
    def add(self, element):
        if not isinstance(element, (DocumentLevelObject, self._Unloaded)):
            raise NineMLRuntimeError(
                "Could not add {} to document '{}' as it is not a 'document "
                "level NineML object' ('{}')"
                .format(element.nineml_type, self.url,
                        "', '".join(self.write_order)))
        if element.name in self:
            # Ignore if the element is already added (this can happen
            # implictly when writing other elements that refer to this element)
            if element is not self[element.name]:
        """

        document = next(instances_of_all_types['Document'].itervalues())
        self.assertRaises(
            NineMLNameError,
            document.add,
            element=None)

    def test_remove_ninemlruntimeerror(self):
        """
        line #: 96
        message: Could not remove {} from document as it is not a document level NineML object ('{}') 

        context:
        --------
    def remove(self, element, ignore_missing=False):
        if not isinstance(element, DocumentLevelObject):
        """

        document = next(instances_of_all_types['Document'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document.remove,
            element=None,
            ignore_missing=False)

    def test__load_elem_from_xml_ninemlruntimeerror(self):
        """
        line #: 217
        message: Circular reference detected in '{}(name={})' element. Resolution stack was:


        context:
        --------
    def _load_elem_from_xml(self, unloaded):
        \"\"\"
        Resolve an element from its XML description and store back in the
        element dictionary
        \"\"\"
        if unloaded in self._loading:
        """

        document = next(instances_of_all_types['Document'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document._load_elem_from_xml,
            unloaded=None)

    def test_standardize_units_ninemlruntimeerror(self):
        """
        line #: 257
        message: Name of unit '{}' conflicts with existing object of differring value or type '{}' and '{}'

        context:
        --------
    def standardize_units(self):
        \"\"\"
        Standardized the units into a single set (no duplicates). Used to avoid
        naming conflicts when writing to file.
        \"\"\"
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
        """

        document = next(instances_of_all_types['Document'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document.standardize_units)

    def test_standardize_units_ninemlruntimeerror2(self):
        """
        line #: 268
        message: Name of dimension '{}' conflicts with existing object of differring value or type '{}' and '{}'

        context:
        --------
    def standardize_units(self):
        \"\"\"
        Standardized the units into a single set (no duplicates). Used to avoid
        naming conflicts when writing to file.
        \"\"\"
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
        """

        document = next(instances_of_all_types['Document'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document.standardize_units)

    def test_from_xml_ninemlxmlerror(self):
        """
        line #: 312
        message: Unrecognised XML namespace '{}', can be one of '{}'

        context:
        --------
    def from_xml(cls, element, url=None, register_url=True, **kwargs):
        xmlns = extract_xmlns(element.tag)
        if xmlns not in ALL_NINEML:
        """

        self.assertRaises(
            NineMLXMLError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_from_xml_ninemlxmlerror2(self):
        """
        line #: 317
        message: '{}' document does not have a NineML root ('{}')

        context:
        --------
    def from_xml(cls, element, url=None, register_url=True, **kwargs):
        xmlns = extract_xmlns(element.tag)
        if xmlns not in ALL_NINEML:
            raise NineMLXMLError(
                "Unrecognised XML namespace '{}', can be one of '{}'"
                .format(xmlns[1:-1],
                        "', '".join(ns[1:-1] for ns in ALL_NINEML)))
        if element.tag[len(xmlns):] != cls.nineml_type:
        """

        self.assertRaises(
            NineMLXMLError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_from_xml_ninemlruntimeerror(self):
        """
        line #: 340
        message: '{}' element does not correspond to a recognised document-level object

        context:
        --------
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
        """

        self.assertRaises(
            NineMLRuntimeError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_from_xml_ninemlxmlerror3(self):
        """
        line #: 354
        message: '{}' is not a valid top-level NineML element

        context:
        --------
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
        """

        self.assertRaises(
            NineMLXMLError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_from_xml_ninemlxmlerror4(self):
        """
        line #: 373
        message: Duplicate identifier '{ob1}:{name}'in NineML file '{url}'

        context:
        --------
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
        """

        self.assertRaises(
            NineMLXMLError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_load_ninemlruntimeerror(self):
        """
        line #: 439
        message: Cannot reuse the '{}' url for two different XML strings

        context:
        --------
    def load(cls, xml, url=None, register_url=True, **kwargs):
        \"\"\"
        Loads the lib9ml object model from a root lxml.etree.Element. If the
        document has been previously loaded it is reused. To reload a document
        that has been changed on file, please delete any references to it first

        xml -- the 'NineML' etree.Element to load the object model
               from
        url -- specifies the url that the xml should be considered
               to have been read from in order to resolve relative
               references
        \"\"\"
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
        """

        self.assertRaises(
            NineMLRuntimeError,
            Document.load,
            xml=None,
            url=None,
            register_url=True)

    def test_url_ninemlruntimeerror(self):
        """
        line #: 464
        message: Cannot reset a documents url to None once it has been set('{}') please duplicate the document instead

        context:
        --------
    def url(self, url):
        if url != self.url:
            if url is None:
        """

        document = next(instances_of_all_types['Document'].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            document.url = None

    def test_url_ninemlruntimeerror2(self):
        """
        line #: 472
        message: Cannot set url of document to '{}' as there is already a document loaded in memory with that url. Please remove all references to it first (see https://docs.python.org/2/c-api/intro.html#objects-types-and-reference-counts)

        context:
        --------
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
        """

        document = next(instances_of_all_types['Document'].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            document.url = None

