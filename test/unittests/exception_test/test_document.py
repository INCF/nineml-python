import unittest
from nineml.document import (Document, read_xml, get_component_class_type)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLXMLError, NineMLNameError,
                               NineMLRuntimeError)
from tempfile import mkdtemp
import os.path
from nineml.xml import Ev1
from nineml.abstraction.dynamics import Trigger
import shutil


class TestDocumentExceptions(unittest.TestCase):

    def setUp(self):
        self._temp_dir = mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_dir)

    def test_read_xml_ninemlruntimeerror(self):
        """
        line #: 582
        message: Could not read 9ML URL '{}': {}
        """

        self.assertRaises(
            NineMLRuntimeError,
            read_xml,
            url='http://this_is_a_bad_url.html',
            relative_to='/a_file.xml')

    def test_read_xml_ninemlruntimeerror2(self):
        """
        line #: 587
        message: Could not parse XML of 9ML file '{}': {}
        """
        bad_xml_path = os.path.join(self._temp_dir, 'bad_xml.xml')
        with open(bad_xml_path, 'w') as f:
            f.write("this file doesn't contain xml")
        self.assertRaises(
            NineMLRuntimeError,
            read_xml,
            url=bad_xml_path,
            relative_to='/a_file.xml')

    def test_get_component_class_type_ninemlxmlerror(self):
        """
        line #: 607
        message: No type defining block in ComponentClass
        """
        elem = Ev1.ComponentClass(name="a")
        self.assertRaises(
            NineMLXMLError,
            get_component_class_type,
            elem=elem)

    def test_add_ninemlruntimeerror(self):
        """
        line #: 66
        message: Could not add {} to document '{}' as it is not a 'document level NineML object' ('{}')
        """
        document = next(
            instances_of_all_types[Document.nineml_type].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document.add,
            element=Trigger('a > b'))

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

        document = instances_of_all_types[Document.nineml_type]['doc1']
        dynB = instances_of_all_types['Dynamics']['dynA'].clone()
        dynB._name = 'dynB'
        self.assertRaises(
            NineMLNameError,
            document.add,
            element=dynB)

    def test_add_ninemlnameerror2(self):
        """
        line #: 84
        message: Attempting to add the same object '{}' {} to '{}' document when it is already in '{}'. Please remove it from the original document first

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
                raise NineMLNameError(
                    "Could not add element '{}' as an element with that name "
                    "already exists in the document '{}'"
                    .format(element.name, self.url))
        else:
            if not isinstance(element, self._Unloaded):
                if element.document is None:
                    element._document = self  # Set its document to this one
                else:
        """

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
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

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document.remove,
            element=None,
            ignore_missing=False)

    def test_remove_ninemlnameerror(self):
        """
        line #: 103
        message: Could not find '{}' element to remove from document '{}'

        context:
        --------
    def remove(self, element, ignore_missing=False):
        if not isinstance(element, DocumentLevelObject):
            raise NineMLRuntimeError(
                "Could not remove {} from document as it is not a document "
                "level NineML object ('{}') ".format(element.nineml_type))
        try:
            del self[element.name]
        except KeyError:
            if not ignore_missing:
        """

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
        self.assertRaises(
            NineMLNameError,
            document.remove,
            element=None,
            ignore_missing=False)

    def test___getitem___ninemlnameerror(self):
        """
        line #: 137
        message: '{}' was not found in the NineML document {} (elements in the document were '{}').

        context:
        --------
    def __getitem__(self, name):
        \"\"\"
        Returns the element referenced by the given name
        \"\"\"
        if name is None:
            # This simplifies code in a few places where an optional
            # attribute refers to a name of an object which
            # should be resolved if present but be set to None if not.
            return None
        try:
            elem = super(Document, self).__getitem__(name)
        except KeyError:
        """

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
        self.assertRaises(
            NineMLNameError,
            document.__getitem__,
            name=None)

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

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
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

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
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

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
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
        line #: 350
        message: Did not find matching NineML class for '{}' element

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
        """

        self.assertRaises(
            NineMLXMLError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_from_xml_ninemlxmlerror4(self):
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

    def test_from_xml_notimplementederror(self):
        """
        line #: 358
        message: Cannot load '{}' element (extensions not implemented)

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
        """

        self.assertRaises(
            NotImplementedError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_from_xml_ninemlxmlerror5(self):
        """
        line #: 369
        message: Missing 'name' (or 'symbol') attribute from document level object '{}'

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
        """

        self.assertRaises(
            NineMLXMLError,
            Document.from_xml,
            element=None,
            url=None,
            register_url=True)

    def test_from_xml_ninemlxmlerror6(self):
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

    def test_write_ninemlruntimeerror(self):
        """
        line #: 395
        message: Cannot write the same Document object to two different locations '{}' and '{}'. Please either explicitly change its `url` property or create a duplicate using the `duplicate` method before attempting to write it to the new location

        context:
        --------
    def write(self, url, version=2.0, **kwargs):
        if self.url is None:
            self.url = url  # Required so relative urls can be generated
        elif self.url != url:
        """

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            document.write,
            url=None,
            version=2.0)

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

    def test_load_ninemlruntimeerror2(self):
        """
        line #: 443
        message: '{}' has been modified between reads. To reload please remove all references to the original version and permit it to be garbarge collected (see https://docs.python.org/2/c-api/intro.html#objects-types-and-reference-counts)

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
                        raise NineMLRuntimeError(
                            "Cannot reuse the '{}' url for two different XML "
                            "strings".format(url))
                    elif saved_time != mod_time:
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

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
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

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            document.url = None

    def test_url_ninemlruntimeerror3(self):
        """
        line #: 488
        message: {} is not a valid URL

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
        """

        document = next(instances_of_all_types[Document.nineml_type].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            document.url = None

