import unittest
from nineml.base import (
    BaseNineMLObject, DynamicPortsObject, ContainerObject,
    accessor_name_from_type)
from nineml.utils.testing.comprehensive import dynA
from nineml.exceptions import (
    NineMLNameError, NineMLInvalidElementTypeException, NineMLRuntimeError)
from nineml.abstraction import Dynamics, Trigger, Parameter
import nineml.units as un


class TestExceptions(unittest.TestCase):

    def test_accessor_name_from_type_ninemlinvalidelementtypeexception(self):
        """
        line #: 537
        message: Could not get member attr for element of type '{}', available
        types are {}
        """
        self.assertRaises(
            NineMLInvalidElementTypeException,
            accessor_name_from_type,
            class_map=Dynamics.class_to_member,
            element_type=Trigger('a > b'))


class TestBaseNineMLObjectExceptions(unittest.TestCase):

    def test_accept_visitor_notimplementederror(self):
        """
        line #: 77
        message: Derived class '{}' has not overriden accept_visitor method.
        """
        self.assertRaises(
            NotImplementedError,
            BaseNineMLObject().accept_visitor,
            visitor=None)


class TestDynamicPortsObjectExceptions(unittest.TestCase):

    def test_port_ninemlnameerror(self):
        """
        line #: 222
        message: '{}' Dynamics object does not have a port named '{}'
        """
        self.assertRaises(
            NineMLNameError,
            dynA.port,
            name='boogiewoogie')
        self.assertRaises(
            NineMLNameError,
            dynA.receive_port,
            name='boogiewoogie')
        self.assertRaises(
            NineMLNameError,
            dynA.send_port,
            name='boogiewoogie')


class TestContainerObjectExceptions(unittest.TestCase):

    def test_add_ninemlruntimeerror(self):
        """
        line #: 346
        message: Could not add '{}' {} to component class as it clashes with
        an existing element of the same name
        """
        self.assertRaises(
            NineMLRuntimeError,
            dynA.add,
            Parameter('P1', un.dimensionless))

    def test_remove_ninemlruntimeerror(self):
        """
        line #: 358
        message: Could not remove '{}' from component class as it was not
        found in member dictionary (use 'ignore_missing' option to ignore)
        """

        self.assertRaises(
            NineMLRuntimeError,
            dynA.remove,
            Parameter('boogiewoogie', un.dimensionless))

    def test_element_ninemlnameerror(self):
        """
        line #: 424
        message: '{}' was not found in '{}' {} object
        """
        self.assertRaises(
            NineMLNameError,
            dynA.element,
            name='boogiewoogie')

    def test___iter___typeerror(self):
        """
        line #: 453
        message: '{}' {} container is not iterable
        """
        self.assertRaises(
            TypeError,
            dynA.__iter__)

