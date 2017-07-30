import os.path
import re
from abc import ABCMeta, abstractmethod
from nineml.exceptions import (
    NineMLSerializationError, NineMLMissingSerializationError,
    NineMLUnexpectedMultipleSerializationError, NineMLNameError)
import nineml
from nineml.reference import Reference
from nineml.base import ContainerObject, DocumentLevelObject
from nineml.annotations import (
    Annotations, INDEX_TAG, INDEX_KEY_ATTR, INDEX_NAME_ATTR, INDEX_INDEX_ATTR,
    PY9ML_NS, VALIDATION, DIMENSIONALITY)
from . import DEFAULT_VERSION, NINEML_BASE_NS


# The name of the attribute used to represent the "namespace" of the element in
# formats that don't support namespaces explicitly.
NS_ATTR = '@namespace'

# The name of the attribute used to represent the "body" of the element in
# formats that don't support element bodies.
# NB: Body elements should be phased out in later 9ML versions to avoid this.
BODY_ATTR = '@body'

# Regex's used in 9ML version string parsing
is_int_re = re.compile(r'\d+(\.0)?')
version_re = re.compile(r'(\d+)\.(\d+)')
nineml_version_re = re.compile(r'{}([\d\.]+)/?'.format(NINEML_BASE_NS))


class BaseVisitor(object):
    """
    Base class for BaseSerializer and BaseUnserializer
    """

    __metaclass__ = ABCMeta

    # A flag to determine whether the serialization form supports element
    # bodies, which is only true of XML amongst the supported formats at this
    # stage.
    supports_bodies = False

    def __init__(self, version, document):
        self._version = self.standardize_version(version)
        self._document = document

    @property
    def version(self):
        return '{}.{}'.format(*self._version)

    @property
    def major_version(self):
        return self._version[0]

    @property
    def minor_version(self):
        return self._version[1]

    @property
    def nineml_namespace(self):
        return 'http://nineml.net/9ML/{}'.format(self.version)

    @property
    def document(self):
        return self._document

    def node_name(self, nineml_cls):
        if (self.major_version == 1 and nineml_cls.v1_nineml_type is not None):
            name = nineml_cls.v1_nineml_type
        else:
            name = nineml_cls.nineml_type
        return name

    @classmethod
    def standardize_version(cls, version):
        try:
            version = float(version)
        except:
            pass
        if isinstance(version, float):
            version = str(version)
        if isinstance(version, str):
            try:
                version = tuple(int(i)
                                for i in version_re.match(version).groups())
            except AttributeError:
                raise NineMLSerializationError(
                    "Invalid NineML version string '{}'".format(version))
        if not isinstance(version, (tuple, list)) and len(version) != 3:
            raise NineMLSerializationError(
                "Unrecognised version - {}".format(version))
        return version

    def later_version(self, version, equal=False):
        for s, o in zip(self._version, self.standardize_version(version)):
            if s > o:
                return True
            elif s < o:
                return False
        return equal


# =============================================================================
# Serialization
# =============================================================================


class BaseSerializer(BaseVisitor):
    """
    Abstract base class for all serializer classes

    Parameters
    ----------
    version : str | int | float
        9ML version to write to
    document : nineml.Document
        Document to serialize or use as a reference when serializing members
        of it
    """

    __metaclass__ = ABCMeta

    def __init__(self, version=DEFAULT_VERSION, document=None, **kwargs):  # @UnusedVariable @IgnorePep8
        if document is None:
            document = nineml.Document()
        super(BaseSerializer, self).__init__(version, document)
        self._root = self.create_root()

    def serialize(self, **options):
        """
        Serializes the document provided to the __init__ method

        Parameters
        ----------
        options : dict(str, object)
            Serialization format-specific options for the method
        """
        self.document.serialize_node(
            NodeToSerialize(self, self.root), **options)
        return self.root

    def visit(self, nineml_object, parent=None, reference=None,
              multiple=False, **options):
        """
        Visits a nineml object and calls its 'serialize_node' method to
        serialize it into the format of the Serializer.

        Parameters
        ----------
        nineml_object : BaseNineMLObject
            The 9ML object to serialize
        parent : <serial-element>
            The serial element within which to create the serialized version
            of the object. If None, the root element is used
        reference : bool | None
            Whether to write the nineml object as a reference (see Reference).
            If None then it is determined by the 'ref_style' kwarg
        ref_style : str
            Can be one of 'force_reference' or 'force_inline',
            'prefer_reference' (default) or 'prefer_inline'
        multiple : bool
            Whether to allow for multiple elements of the same type (important
            for formats such as JSON and YAML which save them in lists)
        options : dict(str, object)
            Serialization format-specific options for the method
        """
        is_doc_level = isinstance(nineml_object, DocumentLevelObject)
        if not is_doc_level:
            assert reference is None, (
                "'reference' kwarg can only be used with DocumentLevelObjects "
                "not {} ({})".format(type(nineml_object), nineml_object))
        serial_elem = None
        # Write object as reference if appropriate
        if parent is not None and is_doc_level and not isinstance(
                nineml_object, Annotations):
            url = self._get_reference_url(nineml_object, reference=reference,
                                          **options)
            if url is not False:  # Write the element as a reference
                serial_elem = self.visit(
                    Reference(nineml_object.name, self.document, url=url),
                    parent=parent, multiple=multiple, **options)
        if serial_elem is None:  # If not written as a reference
            # Set parent to document root if not provided
            if parent is None:
                parent = self.root
            # Create element to hold the serialization
            serial_elem = self.create_elem(
                self.node_name(type(nineml_object)),
                parent=parent, multiple=multiple, **options)
            node = NodeToSerialize(self, serial_elem)
            if self._version[0] == 1 and hasattr(nineml_object,
                                                 'serialize_node_v1'):
                nineml_object.serialize_node_v1(node, **options)
            else:
                nineml_object.serialize_node(node, **options)
            # Append annotations and indices to serialized elem if required
            try:
                save_annotations = (nineml_object.annotations and
                                    not options.get('no_annotations', False))
            except AttributeError:
                save_annotations = False
            save_indices = (isinstance(nineml_object, ContainerObject) and
                            options.get('save_indices', False))
            if save_annotations:
                # Make a clone of the annotations and add save_indices
                annotations = nineml_object.annotations.clone()
            else:
                annotations = Annotations()
            if save_indices:
                # Copy all indices to annotations
                for key, elem, index in nineml_object.all_indices():
                    index_annot = annotations.add((INDEX_TAG, PY9ML_NS))
                    index_annot.set(INDEX_KEY_ATTR, key)
                    index_annot.set(INDEX_NAME_ATTR, elem.key)
                    index_annot.set(INDEX_INDEX_ATTR, index)
                save_annotations = True
            if save_annotations:
                self.visit(annotations, parent=serial_elem, **options)
        return serial_elem

    @property
    def root(self):
        return self._root

    @abstractmethod
    def create_root(self, **options):
        """
        Creates a root serial element

        Parameters
        ----------
        options : dict(str, object)
            Serialization format-specific options for the method
        """

    @abstractmethod
    def create_elem(self, name, parent, multiple=False, namespace=None,
                    **options):
        """
        Creates a serial element within the parent element (in the root element
        if parent is None).

        Parameters
        ----------
        name : str
            The name of the element
        parent : <serial-element>
            The element in which to create the new element
        multiple : bool
            Whether to allow for multiple elements of the same type (important
            for formats such as JSON and YAML which save them in lists)
        namespace : str
            The namespace of the element. For formats that don't support
            namespaces (e.g. JSON, YAML, HDF5) this is stored in a special
            attribute name.
        options : dict(str, object)
            Serialization format-specific options for the method
        """

    @abstractmethod
    def set_attr(self, serial_elem, name, value, **options):
        """
        Set the attribute of a serial element

        Parameters
        ----------
        serial_elem : <serial-element>
            The serial element (dependent on the serialization type)
        name : str
            The name of the attribute
        value : float | int | str
            The value of the attribute
        options : dict(str, object)
            Serialization format-specific options for the method
        """

    @abstractmethod
    def set_body(self, serial_elem, value, **options):
        """
        Set the body of a serial element. For formats that don't support body
        values (e.g. JSON and YAML), the value is stored in an attribute named
        '@body'.

        Parameters
        ----------
        serial_elem : <serial-element>
            The serial element (dependent on the serialization type)
        value : float | int | str
            The value of the attribute
        options : dict(str, object)
            Serialization format-specific options for the method
        """

    @abstractmethod
    def to_file(self, serial_elem, file, **options):  # @ReservedAssignment
        """
        Set the attribute of a serial element

        Parameters
        ----------
        serial_elem : <serial_element>
            Serial element to write to file
        file : file-handle
            File handle in which to write serialized elements
        options : dict(str, object)
            Serialization format-specific options for the method
        """

    @abstractmethod
    def to_str(self, serial_elem, **options):  # @ReservedAssignment
        """
        Set the attribute of a serial element

        Parameters
        ----------
        serial_elem : <serial_element>
            Serial element to write to file
        options : dict(str, object)
            Serialization format-specific options for the method
        """

    def _get_reference_url(self, nineml_object, reference=None,
                           ref_style='prefer', absolute_refs=False, **options):  # @UnusedVariable @IgnorePep8
        """
        Determine whether to write the elemnt as a reference or not depending
        on whether it needs to be, as determined by ``reference``, e.g. in the
        case of populations referenced from projections, or whether the user
        would prefer it to be, ``ref_style``. If neither kwarg is set
        whether the element is written as a reference is determined by whether
        it has already been added to a document or not.

        Parameters
        ----------
        nineml_object: BaseNineMLObject
            The NineML object to write as a reference
        reference : bool | None
            Whether the child should be written as a reference or not. If None
            the ref_style option is used to determine whether it is or not.
        ref_style : (None | 'prefer' | 'force' | 'inline' | 'force_inline' |
                     'local')
            The strategy used to write references if they are not explicitly
            required by the serialization (i.e. for Projections and Selections)
        absolute_refs : bool
            Whether to write references using relative or absolute paths

        Returns
        -------
        url : bool | None
            The url used for the reference if required. If None, the local
            document should be used, if False then the object shouldn't
            be written as a reference
        """
        if ref_style == 'force':
            write_ref = True
        elif ref_style == 'force_inline':
            write_ref = False
        elif reference is not None:
            write_ref = reference
        elif ref_style == 'prefer':
            # Write the element as a reference
            write_ref = True
        elif ref_style == 'inline':
            # Write the element inline
            write_ref = False
        elif ref_style == 'local':
            write_ref = True
        elif ref_style is None:
            # No preference is supplied so the element will be written as
            # a reference if it was loaded from a reference
            write_ref = nineml_object.document is not None
        else:
            raise NineMLSerializationError(
                "Unrecognised ref_style '{}'".format(ref_style))
        # If the element is to be written as a reference and it is not in the
        # current document add it
        if write_ref:
            if (nineml_object.document is None or
                nineml_object.document.url == self.document.url or
                    ref_style == 'local'):  # A local reference
                url = None
            else:
                url = nineml_object.document.url
            # If absolute_refs is not provided (recommended) the relative path
            # is used
            if url is not None and not absolute_refs:
                url = os.path.relpath(nineml_object.document.url,
                                      os.path.dirname(self.document.url))
                # Ensure the relative path starts with the explicit
                # current directory '.'
                if not url.startswith('.'):
                    url = './' + url
        else:
            url = False
        return url


class BaseUnserializer(BaseVisitor):
    """
    Abstract base class for all unserializer classes

    Parameters
    ----------
    root : file | str | <serial-element>
        The root of the document to unserialize, as either a file handle,
        string or preparsed serial element.
    version : str | int | float | None
        The assumed 9ML version of the document, if not provided and root is
        not None then it is extracted from the namespace of the root element.
    url : str
        The url of the document to be unserialized. Used to resolve relative
        reference urls
    class_map : dict(str, type)
        Maps element tags to class types. Used to map element names to
        extension objects.
    document : nineml.Document
        Document to serialize or use as a reference when unserializing elements
        of it
    """

    __metaclass__ = ABCMeta

    def __init__(self, root, version=None, url=None, class_map=None, # @ReservedAssignment @IgnorePep8
                 document=None):
        if class_map is None:
            class_map = {}
        if document is None:
            document = Document(unserializer=self, url=url)
        self._url = url
        # Get root elem either from kwarg or file handle
        if hasattr(root, 'url'):
            self._root = self.from_urlfile(root)
        if isinstance(root, file):
            self._root = self.from_file(root)
        elif isinstance(root, basestring):
            self._root = self.from_str(root)
        else:
            self._root = root
        # Get the version from the root element
        if version is not None:
            version = self.standardize_version(version)
        else:
            if self.root is None:
                raise NineMLSerializationError(
                    "Version needs to be provided if root or file is not")
            extracted_version = self.standardize_version(
                self.extract_version())
            if (version is not None and
                  extracted_version != self.standardize_version(version)):
                raise NineMLSerializationError(
                    "Explicit version {} does not match that of loaded "
                    "root {}".format(extracted_version, version))
            version = extracted_version
        super(BaseUnserializer, self).__init__(version, document=document)
        # Prepare elements in document for lazy loading
        self._doc_elems = {}
        if self.root is not None:
            self._annotation_elem = None
            for nineml_type, elem in self.get_all_children(self.root):
                # Strip out document level annotations
                if nineml_type == self.node_name(Annotations):
                    if self._annotation_elem is not None:
                        raise NineMLSerializationError(
                            "Multiple annotations tags found in document")
                        self._annotation_elem = elem
                    continue
                name = self._get_elem_name(elem)
                # Check for duplicates
                if name in self._doc_elems:
                    raise NineMLSerializationError(
                        "Duplicate elements for name '{}' found in document"
                        .format(name))
                # Get the 9ML class corresponding to the element name
                try:
                    elem_cls = class_map[nineml_type]
                except KeyError:
                    elem_cls = self.get_nineml_class(nineml_type, elem)
                self._doc_elems[name] = (elem, elem_cls)
        self._loaded_elems = []  # keeps track of loaded doc elements

    def unserialize(self):
        """
        Unserializes the root element and all elements underneath it
        """
        for name in self._doc_elems:
            # If a doc element is referenced in another it will be loaded and
            # added to the document so we need to check whether it still needs
            # to be loaded.
            if name not in self._loaded_elems:
                self.load_element(name)
        return self.document

    def load_element(self, name, **options):
        """
        Lazily loads the document-level object named and all elements it
        references

        Parameter
        ---------
        name : str
            Name of the document level object to load
        """
        try:
            serial_elem, nineml_cls = self._doc_elems[name]
        except KeyError:
            raise NineMLNameError(
                "'{}' was not found in the NineML document {} (elements in "
                "the document were '{}').".format(
                    name, self.url or '',
                    "', '".join(self._doc_elems.iterkeys())))
        nineml_object = self.visit(serial_elem, nineml_cls, **options)
        AddToDocumentVisitor(self.document, **options).visit(nineml_object,
                                                             **options)
        self._loaded_elems.append(name)
        return nineml_object

    def visit(self, serial_elem, nineml_cls, allow_ref=False, **options):  # @UnusedVariable @IgnorePep8
        """
        Visits a serial element, unserializes it and returns the resultant
        9ML object

        Parameters
        ----------
        serial_elem : <serial-element>
            The serial element to unserialize
        nineml_cls : type
            The class of the 9ML object to unserialize the serial element to.
            Will call the 'unserialize_node' method of this class on the
            serial element
        allow_ref : bool
            Whether to attempt to load the serial element as a 9ML reference
            (depends on the context it is in)
        options : dict(str, object)
            Serialization format-specific options for the method
        """
        annotations = self._extract_annotations(serial_elem, **options)
        # Set any loading options that are saved as annotations
        self._set_load_options_from_annotations(options, annotations)
        # Create node to wrap around serial element for convenient access in
        # "unserialize" class methods
        node = NodeToUnserialize(self, serial_elem, self.node_name(nineml_cls),
                                 **options)
        # Call the unserialize method of the given class to unserialize the
        # object
        if self._version[0] == 1 and hasattr(nineml_cls,
                                             'unserialize_node_v1'):
            nineml_object = nineml_cls.unserialize_node_v1(node, **options)
        else:
            nineml_object = nineml_cls.unserialize_node(node, **options)
        # Check for unprocessed children/attributes
        if node.unprocessed_children:
            raise NineMLSerializationError(
                "The following unrecognised children '{}' found in the "
                "node that unserialized to {}".format(
                    "', '".join(node.unprocessed_children),
                    repr(nineml_object)))
        if node.unprocessed_attr:
            raise NineMLSerializationError(
                "The following unrecognised attributes '{}' found in the "
                "node that unserialized to {}".format(
                    "', '".join(node.unprocessed_attr), nineml_object))
        if node.unprocessed_body:
            raise NineMLSerializationError(
                "The body of {} node ({}) has not been processed".format(
                    nineml_object, node.unprocessed_body))
        # Set saved indices
        self._set_saved_indices(nineml_object, annotations)
        # Add annotations to nineml object
        nineml_object._annotations = annotations
        return nineml_object

    @property
    def url(self):
        return self._url

    def iterkeys(self):
        return self._doc_elems.iterkeys()

    def keys(self):
        return list(self.iterkeys())

    @property
    def root(self):
        return self._root

    @abstractmethod
    def get_child(self, parent, nineml_type, **options):
        """
        Returns a single child of nineml_type from the parent serial element

        Parameters
        ----------
        parent : <serial-element>
            A serial element to get the children of
        nineml_type : str
            Name of the children to return
        options : dict(str, object)
            Serialization format-specific options for the method

        Returns
        -------
        child : <serial-element>
            A serial element child in the parent serial element
        """

    @abstractmethod
    def get_children(self, parent, nineml_type, **options):
        """
        Iterates over child elements of the given type in the parent
        element

        Parameters
        ----------
        parent : <serial-element>
            A serial element to get the children of
        nineml_type : str
            Name of the children to return
        options : dict(str, object)
            Serialization format-specific options for the method

        Returns
        -------
        children : iterator(<serial-element>)
            An iterator over the children named in the parent serial element
        """

    @abstractmethod
    def get_all_children(self, parent, **options):
        """
        Iterates over all child elements in the parent element together with
        their nineml type in tuples.

        Parameters
        ----------
        parent : <serial-element>
            A serial element to get the children of
        options : dict(str, object)
            Serialization format-specific options for the method

        Returns
        -------
        children : iterator((str, <serial-element>))
            An iterator over all tuples containing the all children and their
            nineml types
        """

    @abstractmethod
    def get_attr(self, serial_elem, name, **options):
        """
        Extracts an attribute from the serial element

        Parameters
        ----------
        serial_elem : <serial-element>
            A serial element
        options : dict(str, object)
            Serialization format-specific options for the method

        Returns
        -------
        attr : str | float | int
            The attribute named
        """

    @abstractmethod
    def get_body(self, serial_elem, **options):
        """
        Extracts the body of the serial element. For formats in which elements
        don't have a body, this is extracted from an attribute named '@body'

        Parameters
        ----------
        serial_elem : <serial-element>
            A serial element
        options : dict(str, object)
            Serialization format-specific options for the method

        Returns
        -------
        body : str | float | int
            The body of the serial element
        """

    @abstractmethod
    def get_attr_keys(self, serial_elem, **options):
        """
        Extracts all attribute names of the serial element

        Parameters
        ----------
        serial_elem : <serial-element>
            A serial element
        options : dict(str, object)
            Serialization format-specific options for the method

        Returns
        -------
        attr : iterable(str)
            An iterator over all attribute names in the element
        """

    @abstractmethod
    def get_namespace(self, serial_elem, **options):
        """
        Extracts the namespace of the serial element. For formats in which
        elements don't have a body, this is extracted from an attribute named
        '@namepace'


        Parameters
        ----------
        serial_elem : <serial-element>
            A serial element
        options : dict(str, object)
            Serialization format-specific options for the method

        Returns
        -------
        namespace : str
            The namespace of the serial element
        """

    @abstractmethod
    def from_file(self, file):  # @ReservedAssignment
        """
        Parses the file and returns the root element

        Parameters
        ----------
        file_ : file handle
            A handle to a file containing the serialized document to
            unserialize

        Returns
        -------
        root : <serial-element>
            The root element of the document
        """

    def from_urlfile(self, urlfile):  # @ReservedAssignment
        """
        Parses the URL file object and returns the root element. Typically this
        is the same as the from_file method, with the exception of the HDF5
        unserializer.

        Parameters
        ----------
        urlfile : URL file handle
            A handle to a URL containing the serialized document to
            unserialize

        Returns
        -------
        root : <serial-element>
            The root element of the document
        """
        return self.from_file(urlfile)

    @abstractmethod
    def from_str(self, string):
        """
        Parses the string and returns the root element

        Parameters
        ----------
        string : str
            A string containing the serialized document to unserialize

        Returns
        -------
        root : <serial-element>
            The root element of the document
        """

    def extract_version(self):
        namespace = self.get_namespace(self.root)
        try:
            version = nineml_version_re.match(namespace).group(1)
        except AttributeError:
            raise NineMLSerializationError(
                "Provided document '{}' is not in a valid 9ML namespace {}"
                .format(self.url, namespace))
        return version

    def _get_elem_name(self, elem):
        """
        Returns the name of an element. NB Units use 'symbol' as their unique
        identifier (from LEMS) all other elements use 'name'
        """
        try:
            try:
                name = self.get_attr(elem, 'name')
            except KeyError:
                name = self.get_attr(elem, 'symbol')
        except KeyError:
            raise NineMLSerializationError(
                "Missing 'name' (or 'symbol') attribute from document "
                "level object '{}' ('{}')".format(
                    elem, "', '".join(self.get_attr_keys(elem))))
        return name

    def get_nineml_class(self, nineml_type, elem, assert_doc_level=True):
        """
        Loads a nineml class from the nineml package. NB that all
        `DocumentLevelObjects` need to be imported into the root nineml package

        Parameters
        ----------
        nineml_type : str
            The name of the nineml class to return
        elem : <serial-element>
            The serial element of which to find the class. Only used for
            component and component-class type objects when using 9MLv1 format.
        assert_doc_level : bool
            Whether to check whether the given nineml_type is a document-level
            object or not.
        """
        try:
            nineml_cls = getattr(nineml, nineml_type)
            if assert_doc_level and not issubclass(nineml_cls,
                                                   DocumentLevelObject):
                raise NineMLSerializationError(
                    "'{}' element does not correspond to a recognised "
                    "document-level object".format(nineml_cls.__name__))
        except AttributeError:
            nineml_cls = None
            if self.major_version == 1:
                if nineml_type == 'ComponentClass':
                    nineml_cls = self._get_v1_component_class_type(elem)
                elif nineml_type == 'Component':
                    nineml_cls = self._get_v1_component_type(elem)
            if nineml_cls is None:
                raise NineMLSerializationError(
                    "Unrecognised element type '{}' found in document"
                    .format(nineml_type))
        return nineml_cls

    def _extract_annotations(self, serial_elem, **options):
        """
        Extract annotations from serial element if present
        """
        try:
            annot_elem = self.get_child(serial_elem, Annotations.nineml_type)
            annot_node = NodeToUnserialize(self, annot_elem, 'Annotations',
                                           check_unprocessed=False)
            annotations = Annotations.unserialize_node(annot_node, **options)
        except NineMLMissingSerializationError:
            annotations = Annotations()  # No annotations found
        return annotations

    def _set_load_options_from_annotations(self, options, annotations):
        """
        Set's load options for classes from annotations
        """
        options['validate_dims'] = annotations.get(
            (VALIDATION, PY9ML_NS), DIMENSIONALITY, default='True') == 'True'

    def _set_saved_indices(self, nineml_object, annotations):
        """
        Extract saved indices from annotations and save them in container
        object.
        """
        if (INDEX_TAG, PY9ML_NS) in annotations:
            for ind in annotations.pop((INDEX_TAG, PY9ML_NS)):
                key = ind.get(INDEX_KEY_ATTR)
                name = ind.get(INDEX_NAME_ATTR)
                index = ind.get(INDEX_INDEX_ATTR)
                nineml_object._indices[
                    key][getattr(nineml_object, key)(name)] = int(index)

    def _get_v1_component_class_type(self, elem):
        """
        Gets the appropriate component-class class for a 9MLv1 component-class.
        NB in 9ML v1 Dynamics, ConnectionRule and RandomDistribution are all
        stored in 'ComponentClass' elements and can only be differentiated by
        the nested 'Dynamics'|'ConnectionRule'|'RandomDistribution' element.
        """
        try:
            nineml_type = next(n for n, _ in self.get_all_children(elem)
                               if n in ('Dynamics', 'ConnectionRule',
                                        'RandomDistribution'))
        except StopIteration:
            raise NineMLSerializationError(
                "No type defining block in ComponentClass ('{}')"
                .format("', '".join(
                    n for n, _ in self.get_all_children(elem))))
        return getattr(nineml, nineml_type)

    def _get_v1_component_type(self, elem):
        """
        Gets the appropriate component class for a 9MLv1 component.
        NB in 9ML v1 DynamicProperties, ConnectionRuleProperties and
        RandomDistributionProperties are all stored in 'Component' elements and
        can only be differentiated by the component class they reference in the
        'Definition' element.
        """
        try:
            defn_elem = self.get_child(elem, 'Prototype')
        except NineMLMissingSerializationError:
            defn_elem = self.get_child(elem, 'Definition')
        name = self.get_body(defn_elem)
        try:
            url = self.get_attr(defn_elem, 'url')
        except KeyError:
            url = None
        if url is not None:
            defn_cls = type(
                Reference(name, self.document, url=url).user_object)
        else:
            try:
                elem_type, doc_elem = next(
                    (t, e) for t, e in self.get_all_children(self.root)
                    if self._get_elem_name(e) == name)
            except StopIteration:
                raise NineMLSerializationError(
                    "Referenced '{}' component or component class is missing "
                    "from document {} ({})"
                    .format(name, self.document.url, "', '".join(
                        self._get_elem_name(e)
                        for _, e in self.get_children(self.root))))
            if elem_type == 'ComponentClass':
                defn_cls = self._get_v1_component_class_type(doc_elem)
            elif elem_type == 'Component':
                return self._get_v1_component_type(doc_elem)
            else:
                raise NineMLSerializationError(
                    "Referenced object '{}' in {} is not component or "
                    "component class it is a {}".format(
                        name, self.document.url, elem_type))
        if issubclass(defn_cls, nineml.user.component.Component):
            cls = defn_cls
        elif defn_cls == nineml.Dynamics:
            cls = nineml.DynamicsProperties
        elif defn_cls == nineml.ConnectionRule:
            cls = nineml.ConnectionRuleProperties
        elif defn_cls == nineml.RandomDistribution:
            cls = nineml.RandomDistributionProperties
        else:
            assert False
        return cls


class BaseNode(object):

    def __init__(self, visitor, serial_elem):
        self._visitor = visitor
        self._serial_elem = serial_elem

    @property
    def visitor(self):
        return self._visitor

    @property
    def serial_element(self):
        return self._serial_elem

    @property
    def version(self):
        return self.visitor.version

    @property
    def document(self):
        return self.visitor.document

    def later_version(self, *args, **kwargs):
        return self.visitor.later_version(*args, **kwargs)


class NodeToSerialize(BaseNode):

    def __init__(self, *args, **kwargs):
        super(NodeToSerialize, self).__init__(*args, **kwargs)
        self.withins = set()
        self.has_ref = False

    def child(self, nineml_object, within=None, reference=None,
              multiple=False, **options):
        """
        Serialize a single nineml_object. optionally "within" a simple
        containing tag.

        Parameters
        ----------
        nineml_object : NineMLObject
            A type of the children to extract from the element
        within : str | NoneType
            The name of the sub-element to extract the child from
        reference : bool | None
            Whether the child should be written as a allow_ref or not. If None
            the ref_style option is used to determine whether it is or not.
            Note that if reference is not False and there is another member
            of the container that can be written as a reference then the
            'children' method with n=1 should be used instead.
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        child_elem : <serial-elem>
            The serialized child element or the 'within' element
        """
        if within is not None:
            if within in self.withins and not multiple:
                raise NineMLSerializationError(
                    "'{}' already added to serialization".format(within))
            serial_elem = self.visitor.create_elem(within,
                                                   parent=self._serial_elem)
            self.withins.add(within)
        else:
            serial_elem = self._serial_elem
        # If the visitor doesn't support body content (i.e. all but XML) and
        # the nineml_object can be flattened into a single attribute
        if (hasattr(nineml_object, 'serialize_body') and
                not self.visitor.supports_bodies):
            self.visitor.set_attr(serial_elem, nineml_object.nineml_type,
                                  nineml_object.serialize_body(**options))
            child_elem = None
        else:
            child_elem = self.visitor.visit(
                nineml_object, parent=serial_elem, reference=reference,
                multiple=multiple, **options)
        return child_elem if within is None else serial_elem

    def children(self, nineml_objects, reference=None, parent_elem=None,
                 sort=True, **options):
        """
        Serialize an iterable (e.g. list or tuple) of nineml_objects of the
        same type. Should be used instead of calling the 'child' method over
        all objects in the iterable.

        Parameters
        ----------
        nineml_objects : list(NineMLObject)
            A type of the children to extract from the element
        reference : bool | None
            Whether the child should be written as a allow_ref or not. If None
            the ref_style option is used to determine whether it is or not.
        parent_elem : <serial-elem>
            The serial element the children will be nested in
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        if parent_elem is None:
            parent_elem = self._serial_elem
        if sort:
            nineml_objects = sorted(nineml_objects, key=lambda o: str(o.key))
        for nineml_object in nineml_objects:
            self.visitor.visit(nineml_object, parent=parent_elem,
                               reference=reference, multiple=True, **options)

    def attr(self, name, value, in_body=False, **options):
        """
        Extract a child of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        name : str
            Name of the attribute
        value : (int | float | str)
            Attribute value
        in_body : bool
            Whether the attribute is within the body of a sub-element (for
            serializations that support body elements, e.g. XML)
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        if in_body and self.visitor.supports_bodies:
            attr_elem = self.visitor.create_elem(
                name, parent=self._serial_elem, multiple=False, **options)
            self.visitor.set_body(attr_elem, value, **options)
        else:
            self.visitor.set_attr(self._serial_elem, name, value, **options)

    def body(self, value, **options):
        """
        Set the body of the elem

        Parameters
        ----------
        value : str | float | int
            The value for the body of the element
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        self.visitor.set_body(self._serial_elem, value, **options)


class NodeToUnserialize(BaseNode):

    def __init__(self, visitor, serial_elem, name, check_unprocessed=True,
                 **options):
        super(NodeToUnserialize, self).__init__(visitor, serial_elem)
        self._name = name
        if check_unprocessed:
            self.unprocessed_attr = set(
                a for a in self.visitor.get_attr_keys(serial_elem, **options)
                if not a.startswith('@'))  # Special attributes start with '@'
            self.unprocessed_children = set(
                n for n, _ in self.visitor.get_all_children(
                    serial_elem, **options))
            self.unprocessed_children.discard(
                self.visitor.node_name(Annotations))
            self.unprocessed_body = (
                self.visitor.get_body(serial_elem, **options) is not None)
        else:
            self.unprocessed_attr = set([])
            self.unprocessed_children = set([])
            self.unprocessed_body = False

    @property
    def name(self):
        return self._name

    def child(self, nineml_classes, within=None, allow_ref=False,
              allow_none=False, allow_within_attrs=False, **options):
        """
        Extract a child of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        nineml_classes : list(type(NineMLObject)) | type(NineMLObject)
            The type(s) of the children to extract from the element
        within : str | NoneType
            The name of the sub-element to extract the child from
        allow_ref : bool | 'only'
            Whether the child is can be a allow_ref or not. If 'only'
            then only allow_refs will be found. Note if there are more than
            one type references possible in a given container then the
            'children' method with n=1 should be used instead.
        allow_none : bool
            Whether the child is allowed to be missing, in which case None
            will be returned
        allow_within_attrs : bool
            Allow 'within' containers to have attributes
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        child : BaseNineMLObject
            Child extracted from the element
        """
        # Create a dictionary mapping nineml_types to the valid nineml classes
        name_map = self._get_name_map(nineml_classes)
        # If the child is nested within another element, find that containing
        # element and use it as the parent elem
        if within is not None:
            try:
                parent_elem = self.visitor.get_child(self._serial_elem, within,
                                                     **options)
                # If the within element is found it cannot be empty
                allow_none = False
                # Check the 'within' element for attributes (it typically
                # shouldn't have any)
                if not allow_within_attrs:
                    if any(not a.startswith('@')
                           for a in self.visitor.get_attr_keys(parent_elem)):
                        raise NineMLSerializationError(
                            "'{}' elements can not have attributes ('{}')"
                            .format(within, "', '".join(
                                self.visitor.get_attr_keys(parent_elem))))
            except NineMLMissingSerializationError:
                if allow_none:
                    return None
                else:
                    raise
            self.unprocessed_children.discard(within)
        else:
            parent_elem = self._serial_elem
        # Check to see if the child has been flattened into an attribute (for
        # classes that are serialized to a single body element in formats that
        # support body content, i.e. XML, such as SingleValue)
        for nineml_cls in name_map.itervalues():
            if (hasattr(nineml_cls, 'unserialize_body') and
                    not self.visitor.supports_bodies):
                try:
                    child = nineml_cls.unserialize_body(
                        self.visitor.get_attr(
                            parent_elem, nineml_cls.nineml_type, **options))
                    self.unprocessed_attr.discard(nineml_cls.nineml_type)
                    return child
                except KeyError:
                    pass
        child = None
        # Check to see if there is a valid reference to the child element
        if allow_ref:
            try:
                ref_elem = self.visitor.get_child(parent_elem,
                                                  Reference.nineml_type)
            except NineMLMissingSerializationError:
                ref_elem = None
            if ref_elem is not None:
                ref = self.visitor.visit(ref_elem, Reference, **options)
                if any(isinstance(ref.user_object, c)
                       for c in name_map.itervalues()):
                    child = ref.user_object
                self.unprocessed_children.discard(Reference.nineml_type)
        # If there were no valid references to the child element look for
        # the child element itself
        if child is None:
            if allow_ref == 'only':
                raise NineMLMissingSerializationError(
                    "Missing reference to '{}' type elements in {}{}"
                    .format("', '".join(name_map),
                            ('{} of '.format(within)
                             if within is not None else ''), self.name))
            child_elems = []
            for nineml_type, cls in name_map.iteritems():
                try:
                    child_elems.append(
                        (cls,
                         self.visitor.get_child(parent_elem, nineml_type)))
                    child_nineml_type = nineml_type
                except NineMLMissingSerializationError:
                    pass
            if len(child_elems) > 1:
                raise NineMLUnexpectedMultipleSerializationError(
                    "Multiple {} children found within {} (found {})"
                    .format('|'.join(name_map), self.name,
                            ', '.join(child_elems)))
            elif not child_elems:
                raise NineMLMissingSerializationError(
                    "No '{}' child found within {}"
                    .format('|'.join(name_map), self.name))
            child_cls, child_elem = child_elems[0]
            child = self.visitor.visit(child_elem, child_cls, **options)
            self.unprocessed_children.discard(child_nineml_type)
        return child

    def children(self, nineml_classes, n='*', allow_ref=False,
                 parent_elem=None, **options):
        """
        Extract a child or children of class 'cls' from the serial
        element 'elem'. The number of expected children is specifed by 'n'.

        Parameters
        ----------
        nineml_classes : list(type(NineMLObject)) | type(NineMLObject)
            The type(s) of the children to extract from the element
        n : int | str
            Either a number, a tuple of allowable numbers or the wildcards
            '+' or '*'
        allow_ref : bool
            Whether the child is expected to be a allow_ref or not.
        parent_elem : <serial-elem>
            The element that the children are nested in
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        children : list(BaseNineMLObject)
            Child extracted from the element
        """
        children = []
        name_map = self._get_name_map(nineml_classes)
        ref_node_name = self.visitor.node_name(Reference)
        if parent_elem is None:
            parent_elem = self._serial_elem
        if allow_ref:
            for ref_elem in self.visitor.get_children(
                    parent_elem, Reference.nineml_type, **options):
                ref = self.visitor.visit(ref_elem, Reference, **options)
                if self.visitor.node_name(type(ref.user_object)) in name_map:
                    children.append(ref.user_object)
                    self.unprocessed_children.discard(ref_node_name)
        for nineml_type, nineml_cls in name_map.iteritems():
            for child_elem in self.visitor.get_children(
                    parent_elem, nineml_type, **options):
                children.append(self.visitor.visit(child_elem, nineml_cls,
                                                   **options))
                self.unprocessed_children.discard(nineml_type)
        if n == '+':
            if not children:
                raise NineMLSerializationError(
                    "Expected at least 1 child of type {} in {} element"
                    .format("|".join(name_map), self.name))
        elif n != '*' and len(children) != n:
            raise NineMLSerializationError(
                "Expected {} child of type {} in {} element"
                .format(n, "|".join(name_map), self.name))
        return children

    def attr(self, name, dtype=str, in_body=False, **options):
        """
        Extract an attribute from the serial element ``elem``.

        Parameters
        ----------
        name : str
            The name of the attribute to retrieve.
        dtype : type
            The type of the returned value
        in_body : bool
            Whether the attribute is within the body of a sub-element (for
            serializations that support body elements, e.g. XML)
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        attr : (int | str | float | bool)
            The attribute to retrieve
        """
        try:
            if in_body and self.visitor.supports_bodies:
                attr_elem = self.visitor.get_child(
                    self._serial_elem, name, **options)
                self.unprocessed_children.remove(name)
                value = self.visitor.get_body(attr_elem, **options)
            else:
                value = self.visitor.get_attr(self._serial_elem, name,
                                              **options)
                self.unprocessed_attr.discard(name)
            try:
                return dtype(value)
            except ValueError:
                raise NineMLSerializationError(
                    "Cannot convert '{}' attribute of {} node ({}) to {}"
                    .format(name, self.name, value, dtype))
        except KeyError:
            try:
                return options['default']
            except KeyError:
                raise NineMLMissingSerializationError(
                    "Node {} does not have required attribute '{}'"
                    .format(self.name, name))

    def body(self, dtype=str, allow_empty=False, **options):
        """
        Returns the body of the serial element

        Parameters
        ----------
        dtype : type
            The type of the returned value
        allow_empty : bool
            Whether the body can be empty

        Returns
        -------
        body : int | float | str
            The return type of the body
        """
        value = self.visitor.get_body(self._serial_elem, **options)
        self.unprocessed_body = False
        if value is None:
            if allow_empty:
                return None
            else:
                raise NineMLSerializationError(
                    "Missing required body of {} node".format(self.name))
        try:
            return dtype(value)
        except ValueError:
            raise NineMLSerializationError(
                "Cannot convert body of {} node ({}) to {}"
                .format(self.name, value, dtype))

    def _get_name_map(self, nineml_classes):
        try:
            nineml_classes = list(nineml_classes)
        except TypeError:
            nineml_classes = [nineml_classes]
        return dict((self.visitor.node_name(c), c) for c in nineml_classes)


from nineml.document import Document, AddToDocumentVisitor  # @IgnorePep8
