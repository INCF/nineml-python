import unittest
from nineml.base import (BaseNineMLObject, ContainerObject)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestBaseNineMLObjectExceptions(unittest.TestCase):

    def test_accept_visitor_notimplementederror(self):
        """
        line #: 77
        message: Derived class '{}' has not overriden accept_visitor method.

        context:
        --------
    def accept_visitor(self, visitor):
        """

        baseninemlobject = next(instances_of_all_types['BaseNineMLObject'].itervalues())
        self.assertRaises(
            NotImplementedError,
            baseninemlobject.accept_visitor,
            visitor=None)


class TestContainerObjectExceptions(unittest.TestCase):

    def test_add_ninemlruntimeerror(self):
        """
        line #: 346
        message: Could not add '{}' {} to component class as it clashes with an existing element of the same name

        context:
        --------
    def add(self, *elements):
        for element in elements:
            dct = self._member_dict(element)
            if element._name in dct:
        """

        containerobject = next(instances_of_all_types['ContainerObject'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            containerobject.add)

    def test___iter___typeerror(self):
        """
        line #: 453
        message: '{}' {} container is not iterable

        context:
        --------
    def __iter__(self):
        """

        containerobject = next(instances_of_all_types['ContainerObject'].itervalues())
        self.assertRaises(
            TypeError,
            containerobject.__iter__)

