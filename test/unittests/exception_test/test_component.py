import unittest
from nineml.user.component import Definition
from nineml.user.dynamics import DynamicsProperties
from nineml.utils.comprehensive_example import dynA, dynB, dynPropA
from nineml.exceptions import (
    NineMLUnitMismatchError, NineMLNameError, NineMLRuntimeError)
from nineml.user import Property, Initial
import nineml.units as un


class TestDefinitionExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 35
        message: Cannot provide name, document or url arguments with explicit
        component class
        """
        self.assertRaises(
            NineMLRuntimeError,
            Definition,
            dynA,
            url='http://nineml.net')

    def test___init___ninemlruntimeerror2(self):
        """
        line #: 44
        message: Wrong number of arguments ({}), provided to Definition
        __init__, can either be one (the component class) or zero
        """
        self.assertRaises(
            NineMLRuntimeError,
            Definition,
            dynA,
            dynB)


class TestDynamicsPropertiesExceptions(unittest.TestCase):

    def test_check_initial_values_ninemlruntimeerror(self):
        """
        line #: 520
        """
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsProperties,
            name='dynPropA',
            definition=dynA,
            properties={
                'P1': -5.56 * un.mV,
                'P2': 78.0 * un.ms,
                'P3': -90.2 * un.mV,
                'P4': 152.0 * un.nA},
            initial_values={
                'SV1': -1.7 * un.V},
            check_initial_values=True)

    def test_check_initial_values_ninemlruntimeerror2(self):
        """
        line #: 526
        message: Dimensions for '{}' initial value, {}, in '{}' don't match
        that of its definition in '{}', {}.
        """
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsProperties,
            name='dynPropA',
            definition=dynA,
            properties={
                'P1': -5.56 * un.mV,
                'P2': 78.0 * un.ms,
                'P3': -90.2 * un.mV,
                'P4': 152.0 * un.nA},
            initial_values={
                'SV1': -1.7 * un.V,
                'SV2': 8.1 * un.mV},
            check_initial_values=True)

    def test_initial_value_ninemlnameerror(self):
        """
        line #: 554
        message: No initial value named '{}' in component class
        """
        self.assertRaises(
            NineMLNameError,
            dynPropA.initial_value,
            name='BadSV')

    def test_set_ninemlnameerror(self):
        """
        line #: 565
        message: '{}' Dynamics does not have a Parameter or StateVariable
        named '{}'
        """
        self.assertRaises(
            NineMLNameError,
            dynPropA.set,
            prop=Property('BadP', 1.0 * un.unitless))

    def test_set_ninemlunitmismatcherror(self):
        """
        line #: 569
        message: Dimensions for '{}' property ('{}') don't match that of
        component_class class ('{}').
        """
        self.assertRaises(
            NineMLUnitMismatchError,
            dynPropA.set,
            prop=Initial('SV1', 1.0 * un.unitless))


class TestComponentExceptions(unittest.TestCase):

    def test___init___valueerror(self):
        """
        line #: 150
        message: 'definition' must be either a 'Definition' or 'Prototype'
        element
        """
        self.assertRaises(
            ValueError,
            DynamicsProperties,
            name='dynProp',
            definition=Property('P1', 1.0 * un.unitless))

    def test_set_ninemlunitmismatcherror(self):
        """
        line #: 201
        message: Dimensions for '{}' property ('{}') don't match that of
        component_class class ('{}').
        """
        self.assertRaises(
            NineMLUnitMismatchError,
            dynPropA.set,
            prop=Property('P1', 1.0 * un.unitless))

    def test_check_properties_ninemlruntimeerror(self):
        """
        line #: 248
        """
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsProperties,
            name='dynPropA',
            definition=dynA,
            properties={
                'P1': -5.56 * un.mV,
                'P2': 78.0 * un.ms,
                'P3': -90.2 * un.mV,
                'P4': 152.0 * un.nA,
                'P5': 0.0 * un.mV},
            initial_values={
                'SV1': -1.7 * un.V,
                'SV2': 8.1 * un.nA})
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsProperties,
            name='dynPropA',
            definition=dynA,
            properties={
                'P1': -5.56 * un.mV,
                'P2': 78.0 * un.ms,
                'P3': -90.2 * un.mV},
            initial_values={
                'SV1': -1.7 * un.V,
                'SV2': 8.1 * un.nA},
            check_initial_values=True)
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsProperties,
            name='dynPropA',
            definition=dynA,
            properties={
                'P1': -5.56 * un.mV,
                'P2': 78.0 * un.ms,
                'P3': -90.2 * un.mV,
                'P5': 0.0 * un.mV},
            initial_values={
                'SV1': -1.7 * un.V,
                'SV2': 8.1 * un.nA})

    def test_check_properties_ninemlruntimeerror2(self):
        """
        line #: 255
        message: Dimensions for '{}' property, {}, in '{}' don't match that
        of its definition in '{}', {}.
        """
        self.assertRaises(
            NineMLRuntimeError,
            DynamicsProperties,
            name='dynPropA',
            definition=dynA,
            properties={
                'P1': -5.56 * un.mV,
                'P2': 78.0 * un.ms,
                'P3': -90.2 * un.mV,
                'P4': 152.0 * un.unitless},
            initial_values={
                'SV1': -1.7 * un.V,
                'SV2': 8.1 * un.nA})

    def test_property_ninemlnameerror(self):
        """
        line #: 380
        message: No property named '{}' in component class
        """
        self.assertRaises(
            NineMLNameError,
            dynPropA.property,
            name='BadProp')

