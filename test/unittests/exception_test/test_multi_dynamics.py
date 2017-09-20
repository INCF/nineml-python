import unittest
from nineml.user.multi.dynamics import MultiDynamics
from nineml.utils.comprehensive_example import dynD, dynE
from nineml.exceptions import NineMLRuntimeError
from nineml.user.multi.port_exposures import AnalogReceivePortExposure
from nineml.user.multi.dynamics import SubDynamics


class TestMultiDynamicsExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 546
        message: Unrecognised port exposure '{}'
        """
        d = SubDynamics('d', dynD)
        e = SubDynamics('e', dynE)
        self.assertRaises(
            NineMLRuntimeError,
            MultiDynamics,
            name='multiDyn',
            sub_components=[d, e],
            port_connections=[
                ('d', 'A1', 'e', 'ARP1'),
                ('e', 'ESP1', 'd', 'ERP1')],
            port_exposures=[AnalogReceivePortExposure('d', 'A1', 'A1_expose')])
