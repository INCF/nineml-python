# encoding: utf-8
"""
Python module for reading/writing 9ML user layer files in XML format.

Functions
---------

    parse - read a 9ML file in XML format and parse it into a Model instance.

Classes
-------
    Model
    Definition
    BaseComponent
        SpikingNodeType
        SynapseType
        CurrentSourceType
        Structure
        ConnectionRule
        ConnectionType
        RandomDistribution
    Parameter
    ParameterSet
    Value
    Group
    Population
    PositionList
    Projection
    Selection
    Operator
        Any
        All
        Not
        Comparison
        Eq
        In


:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from itertools import chain
import urllib
import collections
from numbers import Number
from lxml import etree
from lxml.builder import ElementMaker
from operator import and_
import re
from .. import abstraction_layer
from .containers import Model

nineml_namespace = 'http://nineml.incf.org/9ML/0.3'
NINEML = "{%s}" % nineml_namespace

E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"nineml": nineml_namespace})


def parse(url):
    """
    Read a NineML user-layer file and return a Model object.

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    if not isinstance(url, file):
        f = urllib.urlopen(url)
        doc = etree.parse(f)
        f.close()
    else:
        doc = etree.parse(url)

    root = doc.getroot()
    for import_element in root.findall(NINEML + "import"):
        url = import_element.find(NINEML + "url").text
        imported_doc = etree.parse(url)
        root.extend(imported_doc.getroot().iterchildren())
    return Model.from_xml(root)


def check_tag(element, cls):
    assert element.tag in (cls.element_name, NINEML + cls.element_name), \
                  "Found <%s>, expected <%s>" % (element.tag, cls.element_name)


def walk(obj, visitor=None, depth=0):
    if visitor:
        visitor.depth = depth
    if isinstance(obj, ULobject):
        obj.accept_visitor(visitor)
    if hasattr(obj, "get_children"):
        get_children = obj.get_children
    else:
        get_children = obj.itervalues
    for child in sorted(get_children()):
        walk(child, visitor, depth + 1)


class ExampleVisitor(object):

    def visit(self, obj):
        print " " * self.depth + str(obj)


class Collector(object):

    def __init__(self):
        self.objects = []

    def visit(self, obj):
        self.objects.append(obj)


def flatten(obj):
    collector = Collector()
    walk(obj, collector)
    return collector.objects


class ULobject(object):

    """
    Base class for user layer classes
    """
    children = []

    def __eq__(self, other):
        return reduce(and_, [isinstance(other, self.__class__)] +
                            [getattr(self, name) == getattr(other, name)
                             for name in self.__class__.defining_attributes])

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if self.__class__.__name__ < other.__class__.__name__:
            return True
        else:
            return self.name < other.name

    def get_children(self):
        if hasattr(self, "children"):
            return chain(getattr(self, attr) for attr in self.children)
        else:
            return []

    def accept_visitor(self, visitor):
        visitor.visit(self)
