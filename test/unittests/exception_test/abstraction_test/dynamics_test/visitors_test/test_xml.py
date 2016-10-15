import unittest
from nineml.abstraction.dynamics.visitors.xml import (DynamicsXMLLoader)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLXMLBlockError)


class TestDynamicsXMLLoaderExceptions(unittest.TestCase):

    def test_load_dynamics_ninemlxmlblockerror(self):
        """
        line #: 48
        message: {} blocks should be enclosed in a Dynamics block (i.e. not the outer ComponentClass block) in version 1.0 (they belong in the outer block in later versions)

        context:
        --------
    def load_dynamics(self, element, **kwargs):  # @UnusedVariable
        block_names = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                       'EventSendPort', 'EventReceivePort', 'AnalogReducePort',
                       'Regime', 'Alias', 'StateVariable', 'Constant')
        blocks = self._load_blocks(element, block_names=block_names,
                                   ignore=[(NINEMLv1, 'Dynamics')], **kwargs)
        if extract_xmlns(element.tag) == NINEMLv1:
            if any(blocks[block_name] for block_name in version1_main):
        """

        dynamicsxmlloader = instances_of_all_types['DynamicsXMLLoader']
        self.assertRaises(
            NineMLXMLBlockError,
            dynamicsxmlloader.load_dynamics,
            element=None)

