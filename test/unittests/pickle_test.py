from future import standard_library
standard_library.install_aliases()
import pickle as pkl
import unittest
from nineml.utils.comprehensive_example import instances_of_all_types


class TestPickle(unittest.TestCase):

    def test_pickle(self):
        for obj in instances_of_all_types:
            pkl_str = pkl.dumps(obj)
            unpickled = pkl.loads(pkl_str)
            self.assertEqual(obj, unpickled)
