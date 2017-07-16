import unittest
import tempfile
import os.path
from nineml import read, write
from nineml.utils.testing.comprehensive import dynA, dynB


class TestReadWrite(unittest.TestCase):

    def test_url_resolution(self):
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)
        tmp_path = os.path.join('./test.xml')
        write(tmp_path, dynA, dynB)
        reread_dynA = read('{}#{}'.format(tmp_path, 'dynA'))
        self.assertEqual(dynA, reread_dynA)
