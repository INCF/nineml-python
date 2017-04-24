from abc import ABCMeta, abstractmethod
from nineml.exceptions import NineMLSerializationError

# The name of the attribute used to represent the "body" of the element.
# NB: Body elements should be phased out in later 9ML versions to avoid this.
BODY_ATTRIBUTE = '__body__'

MATHML = "http://www.w3.org/1998/Math/MathML"
UNCERTML = "http://www.uncertml.org/2.0"


class BaseVisitor(object):

    def __init__(self, document, nineml_version):
        self._document = document
        self._version = nineml_version

    @property
    def version(self):
        return self._version

    @property
    def namespace(self):
        return 'http://nineml.net/9ML/{}'.format(float(self.version))

    @property
    def document(self):
        return self._document

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

    def visit(self, nineml_object, parent=None, **options):  # @UnusedVariable
        serial_elem = self.create_elem(self.node_name(type(nineml_object)),
                                       parent=parent, **options)
        node = NodeToSerialize(self, serial_elem)
        nineml_object.serialize(node)
        return node.element

    @abstractmethod
    def create_elem(self, name, parent=None, **options):
        pass

    @abstractmethod
    def set_attr(self, serial_elem, name, value, **options):
        pass

    @abstractmethod
    def set_body(self, serial_elem, value, **options):
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


class NodeToSerialize(BaseNode):

    def __init__(self, *args, **kwargs):
        super(NodeToSerialize, self).__init__(*args, **kwargs)
        self.withins = set()

    def child(self, nineml_object, within=None, reference=False, **options):
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
        reference : bool
            Whether the child should be written as a reference or not
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        if within is not None:
            if within in self.withins:
                raise NineMLSerializationError(
                    "'{}' already added to serialization of {}"
                    .format(within, nineml_object))
            serial_elem = self.visitor.create_elem(self._serial_elem, within)
            self.withins.append(within)
        else:
            serial_elem = self._serial_elem
        self.visitor.visit(nineml_object, parent=serial_elem, **options)

    def children(self, nineml_objects, reference=False, **options):
        """
        Extract a child of class ``cls`` from the serial
        element ``elem``. The number of expected children is specifed by
        ``n``.

        Parameters
        ----------
        nineml_objects : list(NineMLObject)
            A type of the children to extract from the element
        reference : bool
            Whether the child should be written as a reference or not
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)
        """
        for nineml_object in nineml_objects:
            self.visitor.visit(nineml_object, parent=self._serial_elem,
                               **options)

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


class NodeToUnserialize(BaseNode):

    def __init__(self, visitor, serial_elem, nineml_cls):
        super(NodeToUnserialize, self).__init__(visitor, serial_elem)
        self._nineml_cls = nineml_cls
        self.unprocessed = set(self.visitor.get_keys())
        if self.visitor.get_body(serial_elem):
            self.unprocessed.add(BODY_ATTRIBUTE)

    @property
    def nineml_cls(self):
        return self._nineml_cls

    @property
    def name(self):
        return self.visitor.node_name(self.nineml_cls)

    def child(self, nineml_cls, within=None, reference=False, **options):
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
        if within is not None:
            serial_elem = self._get_single_child(self._serial_elem, within)
        else:
            serial_elem = self._serial_elem
        return self.visitor.visit(self._get_single_child(
            serial_elem, self.visitor.node_name(nineml_cls)), **options)

    def children(self, nineml_cls, n='*', reference=False, **options):
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
        for name, elem in self.get_children(self._serial_elem):
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
        self._unprocessed.remove(name)
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
        self._unprocessed.remove(BODY_ATTRIBUTE)
        return dtype(value)

    def _get_single_child(self, elem, name):
        child_elems = [e for n, e in self.get_children(elem)
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
