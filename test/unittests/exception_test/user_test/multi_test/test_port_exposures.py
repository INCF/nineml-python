import unittest
from nineml.user.multi.port_exposures import (_BaseAnalogPortExposure, _LocalAnalogPortConnections, BasePortExposure)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLImmutableError, NineMLRuntimeError)


class Test_BaseAnalogPortExposureExceptions(unittest.TestCase):

    def test_lhs_name_transform_inplace_ninemlimmutableerror(self):
        """
        line #: 156
        message: Cannot rename LHS of Alias '{}' because it is a analog port exposure

        context:
        --------
    def lhs_name_transform_inplace(self, name_map):
        """

        _baseanalogportexposure = instances_of_all_types['_BaseAnalogPortExposure']
        self.assertRaises(
            NineMLImmutableError,
            _baseanalogportexposure.lhs_name_transform_inplace,
            name_map=None)

    def test_set_dimension_ninemlimmutableerror(self):
        """
        line #: 165
        message: Cannot set dimension of port exposure (need to change the dimension of the referenced port).

        context:
        --------
    def set_dimension(self, dimension):
        """

        _baseanalogportexposure = instances_of_all_types['_BaseAnalogPortExposure']
        self.assertRaises(
            NineMLImmutableError,
            _baseanalogportexposure.set_dimension,
            dimension=None)


class Test_LocalAnalogPortConnectionsExceptions(unittest.TestCase):

    def test_lhs_name_transform_inplace_ninemlimmutableerror(self):
        """
        line #: 304
        message: Cannot rename LHS of Alias '{}' because it is a local AnalogPortConnection

        context:
        --------
    def lhs_name_transform_inplace(self, name_map):
        """

        _localanalogportconnections = instances_of_all_types['_LocalAnalogPortConnections']
        self.assertRaises(
            NineMLImmutableError,
            _localanalogportconnections.lhs_name_transform_inplace,
            name_map=None)


class TestBasePortExposureExceptions(unittest.TestCase):

    def test_sub_component_ninemlruntimeerror(self):
        """
        line #: 64
        message: Port exposure is not bound

        context:
        --------
    def sub_component(self):
        if self._sub_component is None:
        """

        baseportexposure = instances_of_all_types['BasePortExposure']
        with self.assertRaises(NineMLRuntimeError):
            print baseportexposure.sub_component

    def test_port_ninemlruntimeerror(self):
        """
        line #: 71
        message: Port exposure is not bound

        context:
        --------
    def port(self):
        if self._port is None:
        """

        baseportexposure = instances_of_all_types['BasePortExposure']
        with self.assertRaises(NineMLRuntimeError):
            print baseportexposure.port

