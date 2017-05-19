import unittest
from nineml.values import ArrayValue
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLValueError, NineMLRuntimeError)
from nineml.document import Document


class TestArrayValueExceptions(unittest.TestCase):

    def test___init___ninemlvalueerror(self):
        """
        line #: 216
        message: Values provided to ArrayValue ({}) could not be converted to a
        """

        for val in instances_of_all_types['ArrayValue'].itervalues():
            self.assertRaises(
                NineMLValueError,
                val.__init__,
                values=['a', 'b', 'c'])

    def test_from_xml_ninemlruntimeerror(self):
        """
        line #: 300
        message: Negative indices found in array rows
        """
        element = E(ArrayValue.nineml_type,
                    E('ArrayValueRow', '1.0', index='-1'))
        self.assertRaises(
            NineMLRuntimeError,
            ArrayValue.from_xml,
            element=element,
            document=Document())

    def test_from_xml_ninemlruntimeerror2(self):
        """
        line #: 304
        message: Duplicate indices ({}) found in array rows
        """
        element = E(ArrayValue.nineml_type,
                    E('ArrayValueRow', '1.0', index='0'),
                    E('ArrayValueRow', '2.0', index='0'))
        self.assertRaises(
            NineMLRuntimeError,
            ArrayValue.from_xml,
            element=element,
            document=Document())

    def test_from_xml_ninemlruntimeerror3(self):
        """
        line #: 308
        message: Indices greater or equal to the number of array rows
        """
        element = E(ArrayValue.nineml_type,
                    E('ArrayValueRow', '1.0', index='2'))
        self.assertRaises(
            NineMLRuntimeError,
            ArrayValue.from_xml,
            element=element,
            document=Document())

    def test___float___typeerror(self):
        """
        line #: 321
        message: ArrayValues cannot be converted to a single float
        """
        for val in instances_of_all_types['ArrayValue'].itervalues():
            self.assertRaises(
                TypeError,
                float,
                val)


class TestRandomValueExceptions(unittest.TestCase):

    def test___float___typeerror(self):
        """
        line #: 457
        message: RandomValues cannot be converted to a single float
        """

        randomvalue = next(instances_of_all_types['RandomValue'].itervalues())
        self.assertRaises(
            TypeError,
            float,
            randomvalue)

    def test___iter___ninemlruntimeerror(self):
        """
        line #: 481
        message: Generator not set for RandomValue '{}'
        """

        randomvalue = next(instances_of_all_types['RandomValue'].itervalues())
        gen = iter(randomvalue)
        self.assertRaises(
            NineMLRuntimeError,
            next,
            gen)

    def test_inverse_notimplementederror(self):
        """
        line #: 503
        message:
        """

        randomvalue = next(instances_of_all_types['RandomValue'].itervalues())
        self.assertRaises(
            NotImplementedError,
            randomvalue.inverse)

