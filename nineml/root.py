# encoding: utf-8
"""
Python module for reading/writing any top level 9ml objects within a NineML
root tag.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from urllib import urlopen
from lxml import etree
from . import E

from .abstraction_layer import ComponentClass
from .user_layer import  Group, Population, Projection  # Unit, UnitDimension, Component @IgnorePep8


class NineMLRoot(object):

    element_tag = 'NineML'

    valid_top_level_elements = [ComponentClass, Group, Population, Projection]
    _elem_lookup = dict((e.element_tag, e) for e in valid_top_level_elements)

    def __init__(self, componentclasses=[], components=[], groups=[],
                 populations=[], projections=[]):
        self.component_classes = dict((c.name, c) for c in componentclasses)
        self.components = dict((c.name, c) for c in components)
        self.groups = dict((g.name, g) for g in groups)
        self.populations = dict((p.name, p) for p in populations)
        self.projections = dict((p.name, p) for p in projections)

    def to_xml(self):
        return E(self.element_tag,
                 *(c.to_xml() for c in self.children))

    @classmethod
    def from_xml(cls, element):
        if element.tag != cls.element_tag:
            raise Exception("Not a NineML root ({})".format(element.tag))
        children = {}
        for child_elem in element.getchildren():
            try:
                child_cls = cls._elem_lookup[child_elem.tag]
                key = child_elem.tag.lower()
                key += 's' if key[-1] != 's' else 'es'
                children[key] = child_cls.from_xml(child_elem)
            except KeyError:
                raise Exception("NineML root element contains invalid element "
                                "'{}'".format(child_elem.tag))
        return cls(**children)

    @classmethod
    def from_file(cls, url):
        """
        Read a NineML file and parse its child elements

        If the URL does not have a scheme identifier, it is taken to refer to a
        local file.
        """
        try:
            if not isinstance(url, file):
                try:
                    f = urlopen(url)
                    xml = etree.parse(f)
                except:  # FIXME: Need to work out what exceptions urlopen raises @IgnorePep8
                    raise Exception("Could not read URL '{}'".format(url))
                finally:
                    f.close()
            else:
                xml = etree.parse(url)
        except:  # FIXME: Need to work out what exceptions etree raises
            raise Exception("Could not parse XML file '{}'".format(url))
        root = xml.getroot()
        try:
            return NineMLRoot.from_xml(root)
        except Exception as e:
            raise Exception("Could not parse NineML file '{}', with error: \n "
                            "{}".format(url, e))
