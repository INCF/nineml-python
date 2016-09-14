import shutil
import os.path
import tempfile
from unittest import TestCase
from copy import deepcopy
import nineml
from nineml.utils.testing.comprehensive import instances_of_all_types
# 
# 
# class TestComprehensiveXML(TestCase):
# 
#     def setUp(self):
#         self._tmp_dir = tempfile.mkdtemp()
# 
#     def tearDown(self):
#         shutil.rmtree(self._tmp_dir)
# 
#     def test_write_read_roundtrip(self):
#         for i, document in enumerate(instances_of_all_types['NineML']):
#             doc = deepcopy(document)
#             url = os.path.join(self._tmp_dir, 'test{}.xml'.format(i))
#             nineml.write(doc, url)
#             reread_doc = nineml.read(url)
#             self.assertEqual(doc, reread_doc,
#                              "Documents don't match, {} and {}"
#                              .format(doc, reread_doc))
