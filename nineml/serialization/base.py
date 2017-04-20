from abc import ABCMeta, abstractmethod


class BaseSerializer(object):
    "Abstract base class for all serializer classes"

    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, *children, **attrs):
        """
        Write given children and attributes into an element in the format
        of the serializer

        Parameters
        ----------
        children : list()
            A list of serialized objects
        attrs : dict(str, (int | str | float | bool))
            A dictionary of attributes to set for the current elem

        Returns
        -------
        elem : <serial-format-element>
            An element in the format of the serialization
        """
        pass


class BaseUnserializer(object):
    "Abstract base class for all unserializer classes"

    __metaclass__ = ABCMeta

    @abstractmethod
    def child(self, elem, cls, n, within=None, **options):
        """
        Extract a child or children of class ``cls`` from the serial element
        ``elem``. The number of expected children is specifed by ``n``.

        Parameters
        ----------
        elem : <serial-format-element>
            The serial-format element to unserialize
        cls : type
            The 9ML type to extract from the elements children
        n : int | str
            Either a number, a tuple of allowable numbers or the wildcards '+'
            or '*'
        within : str | NoneType
            The name of the sub-element to extract the child from
        options : dict
            Options that can be passed to specific branches of the element
            tree (unlikely to be used but included for completeness)

        Returns
        -------
        child : BaseNineMLObject | list(BaseNineMLObject)
            Child or children extracted from the element
        """
        pass

    @abstractmethod
    def attr(self, elem, name, **options):
        """
        Extract a child or children of class ``cls`` from the serial element
        ``elem``. The number of expected children is specifed by ``n``.

        Parameters
        ----------
        elem : <serial-format-element>
            The serial-format element to unserialize
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
        pass
