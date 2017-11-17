import unittest


from nineml.abstraction import (
    AnalogReceivePort, AnalogReducePort, AnalogSendPort, EventReceivePort,
    EventSendPort)
from nineml.exceptions import NineMLUsageError


# Testing Skeleton for class: AnalogPort
class AnalogPort_test(unittest.TestCase):

    def test_name(self):
        # Signature: name
                # The name of the port, local to the current component
        self.assertEqual(AnalogReceivePort('A').name, 'A')
        self.assertEqual(AnalogReducePort('B', operator='+').name, 'B')
        self.assertEqual(AnalogSendPort('C').name, 'C')

    def test_operator(self):
        # Signature: name
                # The reduction operation of the port, if it is a 'reduce' port
        # from nineml.abstraction.component.ports import AnalogPort
        self.assertRaises(
            NineMLUsageError,
            AnalogReducePort, 'V', operator='-')


class EventPort_test(unittest.TestCase):

    def test_name(self):
        self.assertEqual(EventReceivePort('A').name, 'A')
        self.assertEqual(EventSendPort('C').name, 'C')
