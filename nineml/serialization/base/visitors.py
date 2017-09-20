from builtins import zip
from builtins import next
from past.builtins import basestring
from builtins import object
from future.utils import with_metaclass
import os.path
import re
from abc import ABCMeta, abstractmethod
from nineml.exceptions import (
    NineMLSerializationError, NineMLMissingSerializationError, NineMLNameError)
import nineml
from nineml.reference import Reference
from nineml.base import DocumentLevelObject
from nineml.annotations import (
    Annotations, PY9ML_NS, VALIDATION, DIMENSIONALITY)
from .. import DEFAULT_VERSION, NINEML_BASE_NS
from nineml.serialization.base.nodes import NodeToSerialize, NodeToUnserialize
from nineml.utils import is_file_handle


# Regex's used in 9ML version string parsing
is_int_re = re.compile(r'\d+(\.0)?')
version_re = re.compile(r'(\d+)\.(\d+)')
nineml_version_re = re.compile(r'{}([\d\.]+)/?'.format(NINEML_BASE_NS))


class BaseVisitor(with_metaclass(ABCMeta, object)):
    """
    Base class for BaseSerializer and BaseUnserializer
    """

    # The name of the attribute used to represent the "namespace" of the
    # element in formats that don't support namespaces explicitly.
    NS_ATTR = '@namespace'

    # The name of the attribute used to represent the "body" of the element in
    # formats that don't support element bodies. NB: Body elements should be
    # phased out in later 9ML versions to avoid this.
    BODY_ATTR = '@body'

    # Specifies whether a given group represents multiple child elements (i.e.
    # a list) or not
    MULT_ATTR = '@multiple'

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
        if (self.major_version == 1 and nineml_cls.nineml_type_v1 is not None):
            name = nineml_cls.nineml_type_v1
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

    def flat_body(self, nineml_cls):
        return (
            not self.supports_bodies and nineml_cls.has_serial_body == 'only')

    def has_body(self, nineml_cls):
        if nineml_cls.has_serial_body == 'v1':
            has_body = self.major_version == 1
        else:
            has_body = bool(nineml_cls.has_serial_body)
        return has_body


# =============================================================================
# Serialization
# =============================================================================


class BaseSerializer(with_metaclass(ABCMeta, BaseVisitor)):
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

    def __init__(self, version=DEFAULT_VERSION, document=None,
                 preserve_order=False, **kwargs):  # @UnusedVariable @IgnorePep8
        if document is None:
            document = nineml.Document()
        self.preserve_order = preserve_order
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
        serialized = self.root
        return serialized

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
                    Reference(name=nineml_object.name, document=self.document,
                              url=url),
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
            if save_annotations:
                self.visit(nineml_object.annotations, parent=serial_elem,
                           **options)
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

    @classmethod
    def open_file(cls, url):
        return open(url, 'wb')


class BaseUnserializer(with_metaclass(ABCMeta, BaseVisitor)):
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
        elif is_file_handle(root):
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
                    "', '".join(iter(self._doc_elems.keys()))))
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
        # Add annotations to nineml object
        nineml_object._annotations = annotations
        return nineml_object

    @property
    def url(self):
        return self._url

    def keys(self):
        return iter(self._doc_elems.keys())

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
        except TypeError:
            pass
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
            if url.startswith('.'):
                url = os.path.realpath(os.path.join(os.path.dirname(self.url),
                                                    url))
        except KeyError:
            url = None
        if url is not None and url != self.url:
            defn_cls = type(
                Reference(name, self.document, url=url).target)
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
                        for _, e in self.get_all_children(self.root))))
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


from nineml.document import Document, AddToDocumentVisitor  # @IgnorePep8
