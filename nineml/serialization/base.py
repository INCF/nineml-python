import os.path
import re
from abc import ABCMeta, abstractmethod
from nineml.exceptions import (
    NineMLSerializationError, NineMLMissingSerializationError,
    NineMLUnexpectedMultipleSerializationError, NineMLNameError)
from nineml.reference import Reference
from nineml.base import ContainerObject
from nineml.annotations import (
    Annotations, INDEX_TAG, INDEX_KEY_ATTR, INDEX_NAME_ATTR, INDEX_INDEX_ATTR,
    PY9ML_NS, VALIDATION, DIMENSIONALITY)

# The name of the attribute used to represent the "body" of the element.
# NB: Body elements should be phased out in later 9ML versions to avoid this.
BODY_ATTRIBUTE = '__body__'

MATHML = "http://www.w3.org/1998/Math/MathML"
UNCERTML = "http://www.uncertml.org/2.0"

is_int_re = re.compile(r'\d+(\.0)?')
version_re = re.compile(r'(\d+)\.(\d+)')


class BaseVisitor(object):

    def __init__(self, document, version):
        self._document = document
        self._version = self.standardize_version(version)

    @property
    def version(self):
        return '{}.{}'.format(*self._version)

    @property
    def namespace(self):
        return 'http://nineml.net/9ML/{}'.format(self.version)

    @property
    def document(self):
        return self._document

    def node_name(self, nineml_cls):
        if (self._version[0] == 1 and hasattr(nineml_cls, 'v1_nineml_type')):
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

    def later_version(self, *args, **kwargs):
        return self.visitor.later_version(*args, **kwargs)


# =============================================================================
# Serialization
# =============================================================================


class BaseSerializer(BaseVisitor):
    "Abstract base class for all serializer classes"

    __metaclass__ = ABCMeta

    def visit(self, nineml_object, parent=None, as_reference=None, **options):
        if parent is None:
            parent = self.root_elem()
        parent = self.write_reference(nineml_object, parent, as_reference,
                                      **options)
        if parent is None:
            return None  # If wrote reference and object already exists
        serial_elem = self.create_elem(self.node_name(type(nineml_object)),
                                       parent=parent, **options)
        node = NodeToSerialize(self, serial_elem)
        nineml_object.serialize(node, **options)
        # Append annotations and indices to serialized elem if required
        save_annotations = (not options.get('no_annotations', False) and
                            nineml_object.annotations)
        save_indices = (options.get('save_indices', False) and
                        isinstance(nineml_object, ContainerObject))
        if save_indices:
            if save_annotations:
                # Make a clone of the annotations and add save_indices
                annotations = nineml_object.annoations.clone()
            else:
                annotations = Annotations()
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

    @abstractmethod
    def create_elem(self, name, parent=None, **options):
        pass

    @abstractmethod
    def set_attr(self, serial_elem, name, value, **options):
        pass

    @abstractmethod
    def set_body(self, serial_elem, value, **options):
        pass

    @abstractmethod
    def root_elem(self):
        pass

    def write_reference(self, nineml_object, parent, as_reference=None,
                        ref_strategy=None, absolute_refs=False, **options):
        """
        Determine whether to write the elemnt as a reference or not depending
        on whether it needs to be, as determined by `as_ref`, e.g. in the
        case of populations referenced from projections, or whether the user
        would prefer it to be, `prefer_refs`. If neither kwarg is set whether
        the element is written as a reference is determined by whether it
        has already been added to a document or not.

        Parameters
        ----------
        reference : bool | None
            Whether the child should be written as a reference or not. If None
            the ref_strategy option is used to determine whether it is or not.
        ref_strategy : (None | 'prefer' | 'force' | 'inline')
            The strategy used to write references if they are not explicitly
            required by the serialization (i.e. for Projections and Selections)
        absolute_refs : bool
            Whether to write references using relative or absolute paths

        Returns
        -------
        obj_parent : <serial-elem>
            The parent for the nineml_object to be written to, either the
            original parent, the document root or None if the object doesn't
            need to be written
        """
        if as_reference is None:
            if ref_strategy is None:
                # No preference is supplied so the element will be written as
                # a reference if it was loaded from a reference
                as_ref = nineml_object.document is not None
            elif ref_strategy == 'prefer':
                # Write the element as a reference
                as_ref = True
            elif ref_strategy == 'inline':
                # Write the element inline
                as_ref = False
            elif ref_strategy == 'local':
                raise NotImplementedError
            else:
                raise NineMLSerializationError(
                    "Unrecognised ref_strategy '{}'".format(ref_strategy))
        else:
            as_ref = as_reference
        # If the element is to be written as a reference and it is not in the
        # current document add it
        new_parent = None
        if as_ref:
            if nineml_object.document is None:
                try:
                    obj = self.document[self.name]
                    if obj != self:
                        # Cannot write as a reference as an object of that name
                        # already exists in the document
                        if as_reference is None:
                            # If reference was only a preference
                            as_ref = False
                        else:
                            raise NineMLSerializationError(
                                "Cannot add {} to the current document '{}' "
                                "as it clashes with existing object {}"
                                .format(nineml_object, self.document.url,
                                        obj))
                except NineMLNameError:
                    # Add the object to the current document
                    new_parent = self.root_elem()
                    url = None
            else:
                url
        if as_ref:
            # If the object is already in the current document the url is None
            if (nineml_object.document is None or
                nineml_object.document is self.document or
                    nineml_object.document.url == self.document.url):
                url = None
            # Use the full ref if the `absolute_refs` kwarg is provided
            elif absolute_refs:
                url = nineml_object.document.url
            # Otherwise use the relative path, which is recommended as it makes
            # directories of 9ML documents transportable
            else:
                url = os.path.relpath(nineml_object.document.url,
                                      os.path.dirname(self.document.url))
                # Ensure the relative path starts with the explicit
                # current directory '.'
                if not url.startswith('.'):
                    url = './' + url
            # Write the element as a reference
            self.visit(Reference(self.name, self.document, url=url),
                                  parent=parent, **options)
            parent = new_parent
        return parent


class NodeToSerialize(BaseNode):

    def __init__(self, *args, **kwargs):
        super(NodeToSerialize, self).__init__(*args, **kwargs)
        self.withins = set()

    def child(self, nineml_object, within=None, as_reference=None, **options):
        """
        Extract a child of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        nineml_object : NineMLObject
            A type of the children to extract from the element
        within : str | NoneType
            The name of the sub-element to extract the child from
        as_reference : bool | None
            Whether the child should be written as a reference or not. If None
            the ref_strategy option is used to determine whether it is or not.
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        if within is not None:
            if within in self.withins:
                raise NineMLSerializationError(
                    "'{}' already added to serialization of {}"
                    .format(within, nineml_object))
            serial_elem = self.visitor.create_elem(within, self._serial_elem)
            self.withins.add(within)
        else:
            serial_elem = self._serial_elem
        self.visitor.visit(nineml_object, parent=serial_elem,
                           as_reference=as_reference, **options)

    def children(self, nineml_objects, as_reference=None, **options):
        """
        Extract a child of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        nineml_objects : list(NineMLObject)
            A type of the children to extract from the element
        as_reference : bool | None
            Whether the child should be written as a reference or not. If None
            the ref_strategy option is used to determine whether it is or not.
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        for nineml_object in nineml_objects:
            self.visitor.visit(nineml_object, parent=self._serial_elem,
                               as_reference=as_reference, **options)

    def attr(self, name, value, **options):
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
        """
        self.visitor.set_attr(self._serial_elem, name, value, **options)

    def body(self, value, **options):
        """
        Set the body of the elem

        Parameters
        ----------
        value : str | float | int
            The value for the body of the element
        """
        self.visitor.set_body(self._serial_elem, value, **options)


# =============================================================================
# Unserialization
# =============================================================================

class BaseUnserializer(BaseVisitor):
    "Abstract base class for all unserializer classes"

    __metaclass__ = ABCMeta

    def visit(self, serial_elem, nineml_cls, **options):  # @UnusedVariable
        # Extract annotations
        try:
            annot_elem = self.get_single_child(
                serial_elem, self.node_name(Annotations))
            annotations = self.visit(annot_elem, Annotations, **options)
        except NineMLMissingSerializationError:
            annotations = Annotations()
        # Set any loading options that are saved as annotations
        self._set_load_options_from_annotations(options, annotations)
        # Create node to wrap around serial element for convenient access in
        # "unserialize" class methods
        node = NodeToUnserialize(self, serial_elem, nineml_cls)
        # Call the unserialize method of the given class to unserialize the
        # object
        nineml_object = nineml_cls.unserialize(node, **options)
        # Check for unprocessed children/attributes
        if node.unprocessed:
            raise NineMLSerializationError(
                "The following unrecognised children/attributes found in the "
                "node that unserialized to {}".format(
                    "', '".join(node.unprocessed), nineml_object))
        # Set saved indices
        self._set_saved_indices(nineml_object, annotations)
        # Add annotations to nineml object
        nineml_object._annotations = annotations
        return nineml_object

    def get_single_child(self, elem, names=None, **options):
        matches = [(n, e) for n, e in self.get_children(elem, **options)
                   if n != self.node_name(Annotations) and (
                       names is None or n in names)]
        if len(matches) > 1:
            raise NineMLUnexpectedMultipleSerializationError(
                "Multiple {} children found within {} elem"
                .format('|'.join(names), elem))
        elif not matches:
            raise NineMLMissingSerializationError(
                "No '{}' children found within {} elem"
                .format('|'.join(names), elem))
        return matches[0]

    @abstractmethod
    def get_children(self, serial_elem, **options):
        pass

    @abstractmethod
    def get_attr(self, serial_elem, name, **options):
        pass

    @abstractmethod
    def get_body(self, serial_elem, **options):
        pass

    @abstractmethod
    def get_keys(self, serial_elem, **options):
        pass

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


class NodeToUnserialize(BaseNode):

    def __init__(self, visitor, serial_elem, nineml_cls):
        super(NodeToUnserialize, self).__init__(visitor, serial_elem)
        self._nineml_cls = nineml_cls
        self.unprocessed = set(self.visitor.get_keys(serial_elem))
        self.unprocessed.discard(self.node_name(Annotations))
        if self.visitor.get_body(serial_elem):
            self.unprocessed.add(BODY_ATTRIBUTE)

    @property
    def nineml_cls(self):
        return self._nineml_cls

    @property
    def name(self):
        return self.visitor.node_name(self.nineml_cls)

    def child(self, nineml_classes, within=None, reference=False, **options):
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
        reference : bool
            Whether the child is expected to be a reference or not.
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        child : BaseNineMLObject
            Child extracted from the element
        """
        name_map = self._get_name_map(nineml_classes, reference)
        if within is not None:
            _, serial_elem = self.visitor.get_single_child(self._serial_elem,
                                                           within, **options)
            self.unprocessed.remove(within)
        else:
            serial_elem = self._serial_elem
        name, child_elem = self.visitor.get_single_child(
            serial_elem, name_map.keys(), **options)
        if within is None:
            self.unprocessed.remove(name)
        child = self.visitor.visit(child_elem, name_map[name], **options)
        # Dereference Reference if required
        if isinstance(child, Reference):
            if isinstance(child.user_object, nineml_classes):
                child = child.user_object
            else:
                raise NineMLSerializationError(
                    "Found reference {} for unrecognised type {} (accepted {})"
                    .format(child, child.user_object,
                            ", ".join(self.visitor.node_name(c)
                                      for c in nineml_classes)))
        return child

    def children(self, nineml_classes, n='*', reference=False, **options):
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
        reference : bool
            Whether the child is expected to be a reference or not.
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        children : list(BaseNineMLObject)
            Child extracted from the element
        """
        children = []
        name_map = self._get_name_map(nineml_classes, reference)
        for name, elem in self.visitor.get_children(self._serial_elem):
            if name in name_map:
                child = self._visitor.visit(elem, name_map[name], **options)
                # Dereference Reference if required
                if (isinstance(child, Reference) and isinstance(
                        child.user_object, nineml_classes)):
                    child = child.user_object
                children.append(child)
                self.unprocessed.remove(name)
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

    def attr(self, name, dtype=str, **options):
        """
        Extract an attribute from the serial element ``elem``.

        Parameters
        ----------
        name : str
            The name of the attribute to retrieve.
        dtype : type
            The type of the returned value
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        attr : (int | str | float | bool)
            The attribute to retrieve
        """
        value = self.visitor.get_attr(self._serial_elem, name, **options)
        self.unprocessed.remove(name)
        return dtype(value)

    def body(self, dtype=str, **options):
        """
        Returns the body of the serial element

        Parameters
        ----------
        dtype : type
            The type of the returned value

        Returns
        -------
        body : int | float | str
            The return type of the body
        """
        value = self.visitor.get_body(self._serial_elem, **options)
        self.unprocessed.remove(BODY_ATTRIBUTE)
        return dtype(value)

    def _get_name_map(self, nineml_classes, reference):
        try:
            nineml_classes = list(nineml_classes)
        except ValueError:
            nineml_classes = [nineml_classes]
        name_map = {}
        if reference:
            name_map[self.visitor.node_name(Reference)] = Reference
        if reference != 'only':
            name_map.update(
                (self.visitor.node_name(c), c) for c in nineml_classes)
        return name_map
