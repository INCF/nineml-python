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

# The name of the attribute used to represent the "body" of the element.
# NB: Body elements should be phased out in later 9ML versions to avoid this.
BODY_ATTR = '@body'
NS_ATTR = '@namespace'

NINEML_BASE_NS = "http://nineml.net/9ML/"
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
UNCERTML_NS = "http://www.uncertml.org/2.0"

is_int_re = re.compile(r'\d+(\.0)?')
version_re = re.compile(r'(\d+)\.(\d+)')


class BaseVisitor(object):

    __metaclass__ = ABCMeta

    def __init__(self, document, version):
        self._document = document
        self._version = self.standardize_version(version)

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
        if isinstance(version, int):
            version = '{}.0'.format(version)
        elif isinstance(version, float):
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
    "Abstract base class for all serializer classes"

    __metaclass__ = ABCMeta

    def serialize(self, **options):
        self.document.serialize_node(
            NodeToSerialize(self, self.root_elem()), **options)
        return self.root_elem()

    def visit(self, nineml_object, parent=None, reference=None,
              multiple=False, **options):
        is_doc_level = isinstance(nineml_object, DocumentLevelObject)
        if not is_doc_level:
            assert reference is None, (
                "'reference' kwarg can only be used with DocumentLevelObjects "
                "not {} ({})".format(type(nineml_object), nineml_object))
        serial_elem = None
        ref_style = options.get('ref_style', None)
        # Write object as reference if appropriate
        if parent is not None and is_doc_level and ref_style != 'inline':
            url = self.get_reference_url(nineml_object, reference=reference,
                                         **options)
            if url is not False:
                # Write the element as a reference
                serial_elem = self.visit(
                    Reference(nineml_object.name, self.document, url=url),
                    parent=parent, **options)
        if serial_elem is None:  # If not written as a reference
            # Set parent to document root if not provided
            if parent is None:
                parent = self.root_elem()
            serial_elem = self.create_elem(self.node_name(type(nineml_object)),
                                           parent=parent, multiple=multiple,
                                           **options)
            node = NodeToSerialize(self, serial_elem)
            if self.version[0] == 1 and hasattr(nineml_object,
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

    def get_reference_url(self, nineml_object, reference=None,
                          ref_style=None, absolute_refs=False, **options):  # @UnusedVariable @IgnorePep8
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
        ref_style : (None | 'prefer' | 'force' | 'inline')
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
        if reference is None:
            if ref_style is None:
                # No preference is supplied so the element will be written as
                # a reference if it was loaded from a reference
                write_ref = nineml_object.document is not None
            elif ref_style == 'prefer':
                # Write the element as a reference
                write_ref = True
            elif ref_style == 'inline':
                # Write the element inline
                write_ref = False
            elif ref_style == 'local':
                write_ref = True
            else:
                raise NineMLSerializationError(
                    "Unrecognised ref_style '{}'".format(ref_style))
        else:
            write_ref = reference
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

    @abstractmethod
    def create_elem(self, name, parent=None, multiple=False,
                    namespace=None, **options):
        pass

    @abstractmethod
    def set_attr(self, serial_elem, name, value, **options):
        pass

    @abstractmethod
    def set_body(self, serial_elem, value, sole=False, **options):
        pass

    @abstractmethod
    def root_elem(self):
        pass


class BaseUnserializer(BaseVisitor):
    "Abstract base class for all unserializer classes"

    __metaclass__ = ABCMeta

    def __init__(self, version, url, class_map=None):
        if class_map is None:
            class_map = {}
        super(BaseUnserializer, self).__init__(Document(unserializer=self),
                                               version)
        self._url = url
        # Prepare all elements in document for lazy loading
        self._unloaded = {}
        self._annotation_elem = None
        for nineml_type, _, elem in self.get_children(self.root_elem()):
            # Strip out document level annotations
            if nineml_type == self.node_name(Annotations):
                if self._annotation_elem is None:
                    raise NineMLSerializationError(
                        "Multiple annotations tags found in document")
                    self._annotation_elem = elem
                continue
            name = self.get_elem_name(elem)
            # Check for duplicates
            if name in self._unloaded:
                raise NineMLSerializationError(
                    "Duplicate elements for name '{}' found in document"
                    .format(name))
            # Get the 9ML class corresponding to the element name
            try:
                elem_cls = class_map[nineml_type]
            except KeyError:
                elem_cls = self.get_nineml_class(nineml_type, elem)
            self._unloaded[name] = (elem, elem_cls)

    def get_elem_name(self, elem):
        # Units use 'symbol' as their unique identifier (from LEMS) all
        # other elements use 'name'
        try:
            try:
                name = self.get_attr(elem, 'name')
            except KeyError:
                name = self.get_attr(elem, 'symbol')
        except KeyError:
            raise NineMLSerializationError(
                "Missing 'name' (or 'symbol') attribute from document "
                "level object '{}'".format(elem))
        return name

    def unserialize(self):
        for name in self._unloaded:
            self.load_element(name)
        return self.document

    @property
    def url(self):
        return self._url

    def load_element(self, name, **options):
        try:
            serial_elem, nineml_cls = self._unloaded[name]
        except KeyError:
            raise NineMLNameError(
                "'{}' was not found in the NineML document {} (elements in "
                "the document were '{}').".format(
                    name, self.url or '',
                    "', '".join(self._unloaded.iterkeys())))
        nineml_object = self.visit(serial_elem, nineml_cls, **options)
        self.document[name] = nineml_object
        return nineml_object

    def visit(self, serial_elem, nineml_cls, allow_ref=False, **options):  # @UnusedVariable @IgnorePep8
        # Extract annotations if present
        try:
            _, annot_elem = self.get_single_child(
                serial_elem, [self.node_name(Annotations)])
            annot_node = NodeToUnserialize(self, annot_elem, 'Annotations')
            Annotations.unserialize_node(annot_node, **options)
        except NineMLMissingSerializationError:
            annotations = Annotations()  # No annotations found
        # Set any loading options that are saved as annotations
        self._set_load_options_from_annotations(options, annotations)
        # Create node to wrap around serial element for convenient access in
        # "unserialize" class methods
        node = NodeToUnserialize(self, serial_elem, self.node_name(nineml_cls))
        # Call the unserialize method of the given class to unserialize the
        # object
        if self.version[0] == 1 and hasattr(nineml_cls, 'unserialize_node_v1'):
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

    def get_single_child(self, elem, names=None, allow_ref=False, **options):
        if isinstance(names, basestring):
            names = [names]
        child_elems = [
            (n, e) for n, _, e in self.get_children(elem, **options)
            if n != self.node_name(Annotations)]
        if allow_ref != 'only':
            if names is not None:
                matches = [(n, e) for n, e in child_elems if n in names]
            else:
                matches = child_elems
        else:
            matches = []
        if allow_ref:
            ref_name = self.node_name(Reference)
            ref_elems = [e for n, e in child_elems if n == ref_name]
            if names:
                ref_matches = []
                for ref_elem in ref_elems:
                    node = NodeToUnserialize(self, ref_elem, ref_name)
                    ref = Reference.unserialize_node(node, **options)
                    if self.node_name(type(ref.user_object)) in names:
                        ref_matches.append(ref_elem)
            else:
                ref_matches = ref_elems
            matches += [(ref_name, e) for e in ref_matches]
        if len(matches) > 1:
            raise NineMLUnexpectedMultipleSerializationError(
                "Multiple {} children found within {} ({}) (found {})"
                .format('|'.join(names), elem,
                        ', '.join('{}:{}'.format(k, self.get_attr(elem, k))
                                  for k in self.get_attr_keys(elem)),
                        ', '.join(c[0] for c in self.get_children(elem))))
        elif not matches:
            raise NineMLMissingSerializationError(
                "No '{}' child found within {} ({}) (found {})"
                .format('|'.join(names), elem,
                        ', '.join('{}:{}'.format(k, self.get_attr(elem, k))
                                  for k in self.get_attr_keys(elem)),
                        ', '.join(c[0] for c in self.get_children(elem))))
        return matches[0]

    def _set_load_options_from_annotations(self, options, annotations):
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

    def get_nineml_class(self, nineml_type, elem, assert_doc_level=True):
        # Note that all `DocumentLevelObjects` need to be imported
        # into the root nineml package
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

    def _get_v1_component_class_type(self, elem):
        try:
            nineml_type = next(n for n, _, _ in self.get_children(elem)
                               if n in ('Dynamics', 'ConnectionRule',
                                        'RandomDistribution'))
        except StopIteration:
            raise NineMLSerializationError(
                "No type defining block in ComponentClass ('{}')"
                .format("', '".join(n for n, _, _ in self.get_children(elem))))
        return getattr(nineml, nineml_type)

    def _get_v1_component_type(self, elem):
        _, defn_elem = self.get_single_child(elem,
                                             names=('Definition', 'Prototype'))
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
                    (t, e) for t, _, e in self.get_children(self.root_elem())
                    if self.get_elem_name(e) == name)
            except StopIteration:
                raise NineMLSerializationError(
                    "Referenced '{}' component or component class is missing "
                    "from document {}".format(name, self.document.url))
            if elem_type == 'ComponentClass':
                defn_cls = self._get_v1_component_class_type(doc_elem)
            elif elem_type == 'Component':
                return self._get_v1_component_type(doc_elem)
            else:
                raise NineMLSerializationError(
                    "Referenced object '{}' in {} is not component or "
                    "component class it is a {}".format(
                        name, self.document.url, elem_type))
        if defn_cls == nineml.Dynamics:
            cls = nineml.DynamicsProperties
        elif defn_cls == nineml.ConnectionRule:
            cls = nineml.ConnectionRuleProperties
        elif defn_cls == nineml.RandomDistribution:
            cls = nineml.RandomDistributionProperties
        else:
            assert False
        return cls

    @abstractmethod
    def get_children(self, serial_elem, **options):
        pass

    @abstractmethod
    def get_attr(self, serial_elem, name, **options):
        pass

    @abstractmethod
    def get_body(self, serial_elem, sole=True, **options):
        pass

    @abstractmethod
    def get_attr_keys(self, serial_elem, **options):
        pass

    @abstractmethod
    def root_elem(self):
        pass


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
            serial_elem = self.visitor.create_elem(within, self._serial_elem)
            self.withins.add(within)
        else:
            serial_elem = self._serial_elem
        child_elem = self.visitor.visit(nineml_object, parent=serial_elem,
                                        reference=reference, multiple=multiple,
                                        **options)
        return child_elem if within is None else serial_elem

    def children(self, nineml_objects, reference=None, parent_elem=None,
                 **options):
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
        for nineml_object in sorted(nineml_objects, key=lambda o: str(o.key)):
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
        if in_body:
            attr_elem = self.visitor.create_elem(
                name, parent=self._serial_elem, multiple=False, **options)
            self.visitor.set_body(attr_elem, value, **options)
        else:
            self.visitor.set_attr(self._serial_elem, name, value, **options)

    def body(self, value, sole=True, **options):
        """
        Set the body of the elem

        Parameters
        ----------
        value : str | float | int
            The value for the body of the element
        sole : bool
            Whether the body attribute is the sole attribute/child of the
            element (saving within an explicit @body attribute can be avoided
            be in JSON, YAML, HDF5, etc. formats that don't have a notion
            of body)
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        self.visitor.set_body(self._serial_elem, value, sole, **options)


class NodeToUnserialize(BaseNode):

    def __init__(self, visitor, serial_elem, name, **options):
        super(NodeToUnserialize, self).__init__(visitor, serial_elem)
        self._name = name
        self.unprocessed_attr = set(self.visitor.get_attr_keys(serial_elem,
                                                               **options))
        self.unprocessed_children = set(
            n for n, _, _ in self.visitor.get_children(serial_elem, **options))
        self.unprocessed_children.discard(self.visitor.node_name(Annotations))
        self.unprocessed_body = (self.visitor.get_body(serial_elem, sole=False,
                                                       **options) is not None)

    @property
    def name(self):
        return self._name

    def child(self, nineml_classes, within=None, allow_ref=False,
              allow_none=False, **options):
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
            then only allow_refs will be found.
        allow_none : bool
            Whether the child is allowed to be missing, in which case None
            will be returned
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        child : BaseNineMLObject
            Child extracted from the element
        """
        name_map = self._get_name_map(nineml_classes)
        if within is not None:
            try:
                _, serial_elem = self.visitor.get_single_child(
                    self._serial_elem, within, allow_none=allow_none,
                    **options)
                # If the within element is found it cannot be empty
                allow_none = False
            except NineMLMissingSerializationError:
                if allow_none:
                    return None
                else:
                    raise
            self.unprocessed_children.discard(within)
        else:
            serial_elem = self._serial_elem
        try:
            name, child_elem = self.visitor.get_single_child(
                serial_elem, name_map.keys(), allow_ref, **options)
        except NineMLMissingSerializationError:
            if allow_none:
                return None
            else:
                raise
        if within is None:
            self.unprocessed_children.discard(name)
        child = self.visitor.visit(child_elem, name_map.get(name, Reference),
                                   **options)
        # Deallow_ref Reference if required
        if isinstance(child, Reference):
            if isinstance(child.user_object, nineml_classes):
                child = child.user_object
            else:
                raise NineMLSerializationError(
                    "Found allow_ref {} for unrecognised type {} (accepted {})"
                    .format(child, child.user_object,
                            ", ".join(self.visitor.node_name(c)
                                      for c in nineml_classes)))
        return child

    def children(self, nineml_classes, n='*', allow_ref=False,
                 parent_elem=None, **options):
        """
        Extract a child or children of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

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
        for name, _, elem in self.visitor.get_children(parent_elem):
            if name == ref_node_name and allow_ref:
                ref = self._visitor.visit(elem, Reference, **options)
                if self.visitor.node_name(type(ref.user_object)) in name_map:
                    children.append(ref.user_object)
                self.unprocessed_children.discard(ref_node_name)
            elif name in name_map:
                child = self._visitor.visit(elem, name_map[name], **options)
                children.append(child)
                self.unprocessed_children.discard(name)
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
            if in_body:
                _, attr_elem = self.visitor.get_single_child(
                    self._serial_elem, names=name, **options)
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
                raise NineMLSerializationError(
                    "Node {} does not have required attribute '{}'"
                    .format(self.name, name))

    def body(self, dtype=str, allow_empty=False, sole=True, **options):
        """
        Returns the body of the serial element

        Parameters
        ----------
        dtype : type
            The type of the returned value
        allow_empty : bool
            Whether the body can be empty
        sole : bool
            Whether the body attribute is the sole attribute/child of the
            element (saving within an explicit @body attribute can be avoided
            be in JSON, YAML, HDF5, etc. formats that don't have a notion
            of body)

        Returns
        -------
        body : int | float | str
            The return type of the body
        """
        value = self.visitor.get_body(self._serial_elem, sole, **options)
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


from nineml.document import Document  # @IgnorePep8
