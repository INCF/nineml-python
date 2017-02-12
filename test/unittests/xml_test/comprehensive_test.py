import shutil
import os.path
import tempfile
from unittest import TestCase
import nineml
from nineml.utils.testing.comprehensive import (
    instances_of_all_types, v1_safe_docs)


class TestComprehensiveXML(TestCase):

    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp_dir)

    def test_write_read_roundtrip(self):
        for version in (1.0, 2.0):
            if version == 1.0:
                docs = v1_safe_docs
            else:
                docs = instances_of_all_types['NineML'].values()
            for i, document in enumerate(docs):
                doc = document.clone()
                # Add definitions defined inline to document. Ideally this
                # would be done automatically when the containing element is
                # added to the document but will need some generic visitor
                doc.add(doc['popD'].component_class, clone=False)
                doc.add(doc['projA'].response.component_class, clone=False)
#                 doc.add(doc['projC'].response.component_class)
                url = os.path.join(self._tmp_dir,
                                   'test{}v{}.xml'.format(i, version))
                nineml.write(doc, url, version=version)
                reread_doc = nineml.read(url, force_reload=True)
                self.assertTrue(doc.equals(reread_doc),
                                doc.find_mismatch(reread_doc))
