import unittest
from nineml.abstraction.randomdistribution.base import (RandomDistribution)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestRandomDistributionExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 27
        message: Unrecognised random distribution library path '{}'. Available options are '{}'

        context:
        --------
    def __init__(self, name, standard_library, parameters=None,
                 document=None):
        super(RandomDistribution, self).__init__(
            name, parameters, document=document)
        if (not standard_library.startswith(self.standard_library_basepath) or
                standard_library[self._base_len:] not in self.standard_types):
        """

        randomdistribution = instances_of_all_types['RandomDistribution']
        self.assertRaises(
            NineMLRuntimeError,
            randomdistribution.__init__,
            name=None,
            standard_library=None,
            parameters=None,
            document=None)

