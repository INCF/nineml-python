from abc import ABCMeta, abstractmethod
from nineml.exceptions import NineMLSerializationError


class BaseSerializer(object):
    "Abstract base class for all serializer classes"

    __metaclass__ = ABCMeta

    def __init__(self, nineml_version):
        self._version = nineml_version

    def node_name(self, cls):
        if self._version == 1.0 and hasattr(cls, 'v1_nineml_type'):
            name = cls.v1_nineml_type
        else:
            name = cls.nineml_type
        return name

    class Node(object):

        def __init__(self, serializer):
            self._serializer = serializer

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
            self.children([nineml_object], within=within, **options)

        @abstractmethod
        def children(self, nineml_objects, within=None, **options):
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

        @abstractmethod
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


class BaseUnserializer(object):
    "Abstract base class for all unserializer classes"

    __metaclass__ = ABCMeta

    def __init__(self, nineml_version):
        self._version = nineml_version

    def node_name(self, cls):
        if self._version == 1.0 and hasattr(cls, 'v1_nineml_type'):
            name = cls.v1_nineml_type
        else:
            name = cls.nineml_type
        return name

    class Node(object):

        __metaclass__ = ABCMeta

        def __init__(self, serial_elem, unserializer):
            self._serial_elem = serial_elem
            self._unserializer = unserializer
            self.unprocessed_children = set(self._getchildkeys())
            self.unprocessed_attrs = set(self._getattrkeys())

        def node_name(self, cls=None):
            return self._unserializer.node_name(cls if cls is not None
                                                else type(self))

        def child(self, cls, within=None, **options):
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
            return self.children(cls=cls, n=1, within=within, **options)[0]

        def children(self, cls, n, within=None, **options):
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
            for child_elem in self._getchildren(self._serial_elem):
                child_node = type(self)(child_elem, self._unserializer)
                self._unserializer.unserialize(cls, child_node, within,
                                               **options)
            if n == '+':
                if not children:
                    raise NineMLSerializationError(
                        "Expected at least 1 child of type {} in {} element"
                        .format(self.node_name(cls), self.node_name()))
            elif n != '*' or len(children) != n:
                raise NineMLSerializationError(
                    "Expected at {} child of type {} in {} element"
                    .format(n, self.node_name(cls), self.node_name()))
            self._unprocessed.remove(self._unserializer.node_name(cls))

        @abstractmethod
        def attr(self, name):
            """
            Extract an attribute from the serial element ``elem``.

            Parameters
            ----------
            name : str
                The name of the attribute to retrieve
            options : dict
                Options that can be passed to specific branches of the element
                tree (unlikely to be used but included for completeness)

            Returns
            -------
            attr : (int | str | float | bool)
                The attribute to retrieve
            """
            self._unprocessed.remove(name)

        @abstractmethod
        def _getchildren(self, serial_elem):
            pass

        @abstractmethod
        def _getchildkeys(self):
            pass

        @abstractmethod
        def _getattrkeys(self):
            pass
