import unittest
from nineml.user.component import (Definition, DynamicsProperties, Component)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLUnitMismatchError, NineMLRuntimeError)


class TestDefinitionExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 35
        message: Cannot provide name, document or url arguments with explicit component class

        context:
        --------
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            BaseNineMLObject.__init__(self)
            self._referred_to = args[0]
            if kwargs:
        """

        definition = next(instances_of_all_types['Definition'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            definition.__init__)

    def test_to_xml_ninemlruntimeerror(self):
        """
        line #: 61
        message: Cannot create reference for '{}' {} in the provided document due to name clash with existing {} object

        context:
        --------
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        if self.url is None:
            # If definition was created in Python, add component class
            # reference to document argument before writing definition
            try:
                doc_obj = document[self._referred_to.name]
                if doc_obj != self._referred_to:
        """

        definition = next(instances_of_all_types['Definition'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            definition.to_xml,
            document=None,
            E=E)


class TestDynamicsPropertiesExceptions(unittest.TestCase):

    def test_check_initial_values_ninemlruntimeerror(self):
        """
        line #: 526
        message: Dimensions for '{}' initial value, {}, in '{}' don't match that of its definition in '{}', {}.

        context:
        --------
    def check_initial_values(self):
        for var in self.definition.component_class.state_variables:
            try:
                initial_value = self.initial_value(var.name)
            except KeyError:
                raise Exception("Initial value not specified for %s" %
                                var.name)
            initial_units = initial_value.units
            initial_dimension = initial_units.dimension
            var_dimension = var.dimension
            if initial_dimension != var_dimension:
        """

        dynamicsproperties = next(instances_of_all_types['DynamicsProperties'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            dynamicsproperties.check_initial_values)


class TestComponentExceptions(unittest.TestCase):

    def test_set_ninemlunitmismatcherror(self):
        """
        line #: 201
        message: Dimensions for '{}' property ('{}') don't match that of component_class class ('{}').

        context:
        --------
    def set(self, prop):
        param = self.component_class.parameter(prop.name)
        if prop.units.dimension != param.dimension:
        """

        component = next(instances_of_all_types['Component'].itervalues())
        self.assertRaises(
            NineMLUnitMismatchError,
            component.set,
            prop=None)

    def test_check_properties_ninemlruntimeerror(self):
        """
        line #: 248
        message: . 

        context:
        --------
    def check_properties(self):
        # First check the names
        properties = set(self.property_names)
        parameters = set(self.component_class.parameter_names)
        msg = []
        diff_a = properties.difference(parameters)
        diff_b = parameters.difference(properties)
        if diff_a:
            msg.append("User properties of '{}' ({}) contain the following "
                       "parameters that are not present in the definition of "
                       "'{}' ({}): {}\n\n".format(
                           self.name, self.url, self.component_class.name,
                           self.component_class.url, ",".join(diff_a)))
        if diff_b:
            msg.append("Definition of '{}' ({}) contains the following "
                       "parameters that are not present in the user properties"
                       " of '{}' ({}): {}".format(
                           self.component_class.name, self.component_class.url,
                           self.name, self.url, ",".join(diff_b)))
        if msg:
            # need a more specific type of Exception
        """

        component = next(instances_of_all_types['Component'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            component.check_properties)

    def test_check_properties_ninemlruntimeerror2(self):
        """
        line #: 255
        message: Dimensions for '{}' property, {}, in '{}' don't match that of its definition in '{}', {}.

        context:
        --------
    def check_properties(self):
        # First check the names
        properties = set(self.property_names)
        parameters = set(self.component_class.parameter_names)
        msg = []
        diff_a = properties.difference(parameters)
        diff_b = parameters.difference(properties)
        if diff_a:
            msg.append("User properties of '{}' ({}) contain the following "
                       "parameters that are not present in the definition of "
                       "'{}' ({}): {}\n\n".format(
                           self.name, self.url, self.component_class.name,
                           self.component_class.url, ",".join(diff_a)))
        if diff_b:
            msg.append("Definition of '{}' ({}) contains the following "
                       "parameters that are not present in the user properties"
                       " of '{}' ({}): {}".format(
                           self.component_class.name, self.component_class.url,
                           self.name, self.url, ",".join(diff_b)))
        if msg:
            # need a more specific type of Exception
            raise NineMLRuntimeError(". ".join(msg))
        # Check dimensions match
        for param in self.component_class.parameters:
            prop_units = self.property(param.name).units
            prop_dimension = prop_units.dimension
            param_dimension = param.dimension
            if prop_dimension != param_dimension:
        """

        component = next(instances_of_all_types['Component'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            component.check_properties)

