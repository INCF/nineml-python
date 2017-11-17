from builtins import object
from nineml.exceptions import (
    NineMLSerializationError, NineMLMissingSerializationError,
    NineMLUnexpectedMultipleSerializationError)
from nineml.reference import Reference
from nineml.annotations import Annotations
from nineml.utils import validate_identifier


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
        if self.visitor.flat_body(nineml_object):
            mock_node = MockNodeToSerialize()
            nineml_object.serialize_node(mock_node, **options)
            self.visitor.set_attr(serial_elem, nineml_object.nineml_type,
                                  mock_node._body)
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
        if sort and not self.visitor.preserve_order:
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
        self._name = validate_identifier(name)
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
        for nineml_cls in name_map.values():
            if self.visitor.flat_body(nineml_cls):
                try:
                    mock_node = MockNodeToUnSerialize(self.visitor.get_attr(
                        parent_elem, nineml_cls.nineml_type, **options))
                    child = nineml_cls.unserialize_node(mock_node, **options)
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
                if any(isinstance(ref.target, c)
                       for c in name_map.values()):
                    child = ref.target
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
            for nineml_type, cls in name_map.items():
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
                if self.visitor.node_name(type(ref.target)) in name_map:
                    children.append(ref.target)
                    self.unprocessed_children.discard(ref_node_name)
        for nineml_type, nineml_cls in name_map.items():
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


class MockNodeToSerialize(object):

    def body(self, body, **options):  # @UnusedVariable
        self._body = body


class MockNodeToUnSerialize(object):

    def __init__(self, body):
        self._body = body

    def body(self, dtype=str, **options):  # @UnusedVariable
        return dtype(self._body)
