from abc import ABCMeta, abstractmethod
from nineml.exceptions import NineMLSerializationError


class BaseVisitor(object):

    def __init__(self, nineml_version):
        self._version = nineml_version

    @property
    def version(self):
        return self._version

    def node_name(self, nineml_cls):
        if (self.version == 1.0 and
                hasattr(nineml_cls, 'v1_nineml_type')):
            name = nineml_cls.v1_nineml_type
        else:
            name = nineml_cls.nineml_type
        return name


class BaseSerializer(BaseVisitor):
    "Abstract base class for all serializer classes"

    __metaclass__ = ABCMeta

    def visit(self, parent_elem, nineml_object, **options):  # @UnusedVariable
        serial_elem = self._add_child_elem(parent_elem,
                                           self.node_name(type(nineml_object)))
        node = NodeToSerialize(self, serial_elem)
        nineml_object.serialize(node)

    @abstractmethod
    def _add_child_elem(self, parent_elem, name):
        pass

    @abstractmethod
    def _add_child(self, serial_elem, name, child_elem, **options):
        pass

    @abstractmethod
    def _set_attr(self, serial_elem, name, value, **options):
        pass


class BaseUnserializer(BaseVisitor):
    "Abstract base class for all unserializer classes"

    __metaclass__ = ABCMeta

    def visit(self, serial_elem, nineml_cls, **options):  # @UnusedVariable
        node = NodeToUnserialize(self, serial_elem, nineml_cls)
        nineml_object = nineml_cls.unserialize(node)
        if node.unprocessed:
            raise NineMLSerializationError(
                "The following unrecognised children/attributes found in the "
                "node that unserialized to {}".format(
                    "', '".join(node.unprocessed), nineml_object))
        return nineml_object

    @abstractmethod
    def _get_children(self, serial_elem):
        pass

    @abstractmethod
    def _get_attr(self, serial_elem, name, **options):
        pass

    @abstractmethod
    def _get_keys(self):
        pass


class BaseNode(object):

    def __init__(self, visitor, serial_elem):
        self._visitor = visitor
        self._serial_elem = serial_elem

    @property
    def visitor(self):
        return self._visitor


class NodeToSerialize(BaseNode):

    def __init__(self, *args, **kwargs):
        super(NodeToSerialize, self).__init__(*args, **kwargs)
        self.withins = set()

    def nineml_cls(self):
        return type(self._nineml_object)

    def child(self, nineml_object, within=None, **options):
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
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        if within is not None:
            if within in self.withins:
                raise NineMLSerializationError(
                    "'{}' already added to serialization of {}"
                    .format(within, nineml_object))
            serial_elem = self.visitor._add_child_elem(self._serial_elem,
                                                       within)
            self.withins.append(within)
        else:
            serial_elem = self._serial_elem
        self.visitor._add_child(
            serial_elem,
            self.visitor.visit(nineml_object, **options), **options)

    def children(self, nineml_objects, **options):
        """
        Extract a child of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        nineml_objects : list(NineMLObject)
            A type of the children to extract from the element
        within : str | NoneType
            The name of the sub-element to extract the child from
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        for nineml_object in nineml_objects:
            self.visitor._add_child(
                self._serial_elem,
                self.visitor.visit(nineml_object, **options), **options)

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
        self.visitor._set_attr(self._serial_elem, name, value, **options)


class NodeToUnserialize(BaseNode):

    def __init__(self, visitor, serial_elem, nineml_cls):
        super(NodeToUnserialize, self).__init__(visitor, serial_elem)
        self._nineml_cls = nineml_cls
        self.unprocessed = set(self._getkeys())

    @property
    def nineml_cls(self):
        return self._nineml_cls

    @property
    def name(self):
        return self.visitor.node_name(self.nineml_cls)

    def child(self, nineml_cls, within=None, **options):
        """
        Extract a child of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        cls : type(NineMLObject)
            A type of the children to extract from the element
        within : str | NoneType
            The name of the sub-element to extract the child from
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        child : BaseNineMLObject
            Child extracted from the element
        """
        if within is not None:
            serial_elem = self._get_single_child(self._serial_elem, within)
        else:
            serial_elem = self._serial_elem
        return self.visitor.visit(self._get_single_child(
            serial_elem, self.visitor.node_name(nineml_cls)), **options)

    def children(self, nineml_cls, n, **options):
        """
        Extract a child or children of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        cls : type(NineMLObject)
            A type of the children to extract from the element
        n : int | str
            Either a number, a tuple of allowable numbers or the wildcards
            '+' or '*'
        within : str | NoneType
            The name of the sub-element to extract the child from
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        children : list(BaseNineMLObject)
            Child extracted from the element
        """
        children = []
        for name, elem in self._get_children(self._serial_elem):
            if name == self.name:
                children.append(
                    self._visitor.visit(elem, nineml_cls, **options))
        if n == '+':
            if not children:
                raise NineMLSerializationError(
                    "Expected at least 1 child of type {} in {} element"
                    .format(self.visitor.node_name(nineml_cls), self.name))
        elif n != '*' and len(children) != n:
            raise NineMLSerializationError(
                "Expected {} child of type {} in {} element"
                .format(n, self.visitor.node_name(nineml_cls), self.name))
        self._unprocessed.remove(self.visitor.node_name(nineml_cls))
        return children

    def attr(self, name, **options):
        """
        Extract an attribute from the serial element ``elem``.

        Parameters
        ----------
        name : str
            The name of the attribute to retrieve.
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        attr : (int | str | float | bool)
            The attribute to retrieve
        """
        value = self.visitor._get_attr(self._serial_elem, name, **options)
        self._unprocessed.remove(name)
        return value

    def _get_single_child(self, elem, name):
        child_elems = [e for n, e in self._get_children(elem)
                       if n == name]
        if len(child_elems) > 1:
            raise NineMLSerializationError(
                "Multiple '{}' children found within {} elem"
                .format(name, elem))
        elif not child_elems:
            raise NineMLSerializationError(
                "No '{}' children found within {} elem"
                .format(name, elem))
        return child_elems[0]
