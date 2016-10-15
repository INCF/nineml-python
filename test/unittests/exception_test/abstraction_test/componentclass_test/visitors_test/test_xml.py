import unittest
from nineml.abstraction.componentclass.visitors.xml import (ComponentClassXMLLoader)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLXMLBlockError)


class TestComponentClassXMLLoaderExceptions(unittest.TestCase):

    def test__load_blocks_ninemlxmlblockerror(self):
        """
        line #: 88
        message: Unexpected block {} within {} in '{}', expected: {}

        context:
        --------
    def _load_blocks(self, element, block_names, unprocessed=None,
                     prev_block_names={}, ignore=[], **kwargs):  # @UnusedVariable @IgnorePep8
        \"\"\"
        Creates a dictionary that maps class-types to instantiated objects
        \"\"\"
        # Get the XML namespace (i.e. NineML version)
        xmlns = extract_xmlns(element.tag)
        assert xmlns in ALL_NINEML
        # Initialise loaded objects with empty lists
        loaded_objects = dict((block, []) for block in block_names)
        for t in element.iterchildren(tag=etree.Element):
            # Used in unprocessed_xml decorator
            if unprocessed:
                unprocessed[0].discard(t)
            # Strip namespace
            tag = (t.tag[len(xmlns):]
                   if t.tag.startswith(xmlns) else t.tag)
            if (xmlns, tag) not in ignore:
                if tag not in block_names:
        """

        componentclassxmlloader = instances_of_all_types['ComponentClassXMLLoader']
        self.assertRaises(
            NineMLXMLBlockError,
            componentclassxmlloader._load_blocks,
            element=None,
            block_names=None,
            unprocessed=None,
            prev_block_names={},
            ignore=[])

