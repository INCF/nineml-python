from __future__ import absolute_import
from builtins import zip
import re
import math
from logging import getLogger

logger = getLogger('NineML')


def nearly_equal(float1, float2, places=15):
    """
    Determines whether two floating point numbers are nearly equal (to
    within reasonable rounding errors
    """
    mantissa1, exp1 = math.frexp(float1)
    mantissa2, exp2 = math.frexp(float2)
    return (round(mantissa1, places) == round(mantissa2, places) and
            exp1 == exp2)

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'\{(.*)\}(.*)')


def strip_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(2)


def xml_equal(xml1, xml2, indent='', annotations=False):
    if xml1.tag != xml2.tag:
        logger.error("{}Tag '{}' doesn't equal '{}'"
                     .format(indent, xml1.tag, xml2.tag))
        return False
    if xml1.attrib != xml2.attrib:
        logger.error("{}Attributes '{}' doesn't equal '{}'"
                     .format(indent, xml1.attrib, xml2.attrib))
        return False
    text1 = xml1.text if xml1.text is not None else ''
    text2 = xml2.text if xml2.text is not None else ''
    if text1.strip() != text2.strip():
        logger.error("{}Body '{}' doesn't equal '{}'"
                     .format(indent, text1, text2))
        return False
    tail1 = xml1.tail if xml1.tail is not None else ''
    tail2 = xml2.tail if xml2.tail is not None else ''
    if tail1.strip() != tail2.strip():
        if text1.strip() != text2.strip():
            logger.error("{}Body '{}' doesn't equal '{}'"
                         .format(indent, tail1, tail2))
        return False
    children1 = [c for c in xml1.getchildren()
                 if not c.tag.endswith('Annotations') or annotations]
    children2 = [c for c in xml2.getchildren()
                 if not c.tag.endswith('Annotations') or annotations]
    if len(children1) != len(children2):
        logger.error("{}Number of children {} doesn't equal {}:\n{}\n{}"
                     .format(indent, len(children1), len(children2),
                             ', '.join(
                                 '{}:{}'.format(strip_xmlns(c.tag),
                                                c.attrib.get('name', None))
                                 for c in children1),
                             ', '.join(
                                 '{}:{}'.format(strip_xmlns(c.tag),
                                                c.attrib.get('name', None))
                                 for c in children2)))
        return False
    return all(xml_equal(c1, c2, indent=indent + '    ')
               for c1, c2 in zip(children1, children2))
