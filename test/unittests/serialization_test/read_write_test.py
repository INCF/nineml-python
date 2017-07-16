import unittest
import tempfile
import os
from nineml import read, write
from nineml import DynamicsProperties
from nineml.utils.testing.comprehensive import dynA, dynB


class TestReadWrite(unittest.TestCase):

    tmp_path = './test.xml'

    def test_url_resolution(self):
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)
        write(self.tmp_path, dynA, dynB)
        reread_dynA = read('{}#dynA'.format(self.tmp_path))
        self.assertEqual(dynA, reread_dynA)
        # Read again using document cache via Dynamics Properties
        dynBProps = DynamicsProperties(
            name='dynBProps',
            definition='{}#dynB'.format(os.path.join(tmp_dir, self.tmp_path)),
            properties={'P1': 1, 'P2': 2, 'P3': 3})
        self.assertEqual(dynB, dynBProps.component_class)
