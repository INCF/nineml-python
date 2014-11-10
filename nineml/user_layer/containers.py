from itertools import chain
from operator import itemgetter
from .base import BaseULObject, NINEML, E
from utility import check_tag
from ..utility import expect_single


def find_difference(this, that):
    assert isinstance(that, this.__class__)
    if this != that:
        if isinstance(this, BaseULObject):
            for attr in this.defining_attributes:
                a = getattr(this, attr)
                b = getattr(that, attr)
                if a != b:
                    print this, attr, this.children
                    if attr in this.children:
                        find_difference(a, b)
                    else:
                        errmsg = ("'%s' attribute of %s instance '%s' differs:"
                                  " '%r' != '%r'" % (attr,
                                                     this.__class__.__name__,
                                                     this.name, a, b))
                        if type(a) != type(b):
                            errmsg += "(%s, %s)" % (type(a), type(b))
                        raise Exception(errmsg)
        else:
            assert sorted(this.keys()) == sorted(
                that.keys())  # need to handle case of different keys
            for key in this:
                find_difference(this[key], that[key])


class Selection(BaseULObject):

    """
    Container for combining multiple populations or subsets thereof
    """
    element_name = "Selection"

    def __init__(self, name, operation):
        self.name = name
        self.operation = operation
        self._from_reference = False

    def _to_xml(self):
        return E(self.element_name,
                 self.operation.to_xml(),
                 name=self.name)

    @classmethod
    def from_xml(cls, element, context):
        check_tag(element, cls)
        # The only supported op at this stage
        op = Concatenate.from_xml(expect_single(element.findall(NINEML +
                                                               'Concatenate')),
                                  context)
        return cls(element.attrib['name'], op)


class Concatenate(BaseULObject):
    """
    Concatenates multiple Populations or Selections together into
    a greater Selection
    """

    element_name = 'Concatenate'

    def __init__(self, *items):
        self._items = items

    @property
    def items(self):
        return self._items

    def to_xml(self):
        return E(self.element_name,
                 *[E.Item(item, index=str(i))
                   for i, item in enumerate(self.items)])

    @classmethod
    def from_xml(cls, element, context):
        # Load references and indices from xml
        items = ((e.attrib['index'], context.resolve_ref(e))
                 for e in element.findall(NINEML + 'Item'))
        # Sort by 'index' attribute
        indices, items = zip(*sorted(items, key=itemgetter(0)))
        indices = [int(i) for i in indices]
        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate indices found in Concatenate list ({})"
                             .format(indices))
        if indices[0] != 0:
            raise ValueError("Indices of Concatenate items must start from 0 "
                             "({})".format(indices))
        if indices[-1] != len(indices) - 1:
            raise ValueError("Missing indices in Concatenate items ({}), list "
                             "must be contiguous.".format(indices))
        return cls(items)  # Strip off indices used to sort elements


class Network(BaseULObject):

    """
    Container for populations and projections between those populations. May be
    used as the node cell within a population, allowing hierarchical
    structures.
    """
    element_name = "Network"
    defining_attributes = ("name", "populations", "projections", "selections")
    children = ("populations", "projections", "selections")

    def __init__(self, name, populations={}, projections={}, selections={}):
        self.name = name
        self.populations = populations
        self.projections = projections
        self.selections = selections

    def add(self, *objs):
        """
        Add one or more Population, Projection or Selection instances to the
        network.
        """
        for obj in objs:
            if isinstance(obj, Population):
                self.populations[obj.name] = obj
            elif isinstance(obj, Projection):
                self.projections[obj.name] = obj
            elif isinstance(obj, Selection):
                self.selections[obj.name] = obj
            else:
                raise Exception("Networks may only contain Populations, "
                                "Projections, or Selections")

    def _resolve_population_references(self):
        for prj in self.projections.values():
            for name in ('source', 'target'):
                if prj.references[name] in self.populations:
                    obj = self.populations[prj.references[name]]
                elif prj.references[name] in self.selections:
                    obj = self.selections[prj.references[name]]
                elif prj.references[name] == self.name:
                    obj = self
                else:
                    raise Exception("Unable to resolve population/selection "
                                    "reference ('%s') for %s of %s" %
                                    (prj.references[name], name, prj))
                setattr(prj, name, obj)

    def get_components(self):
        components = []
        for p in chain(self.populations.values(), self.projections.values()):
            components.extend(p.get_components())
        return components

    def get_subnetworks(self):
        return [p.cell for p in self.populations.values()
                if isinstance(p.cell, Network)]

    def _to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[p.to_xml() for p in chain(self.populations.values(),
                                             self.selections.values(),
                                             self.projections.values())])

    @classmethod
    def from_xml(cls, element, context):
        check_tag(element, cls)
        populations = []
        for pop_elem in element.findall(NINEML + 'PopulationItem'):
            pop = context.resolve_ref(pop_elem, Population)
            populations[pop.name] = pop
        projections = []
        for proj_elem in element.findall(NINEML + 'ProjectionItem'):
            proj = context.resolve_ref(proj_elem, Projection)
            projections[proj.name] = proj
        selections = []
        for sel_elem in element.findall(NINEML + 'SelectionItem'):
            sel = context.resolve_ref(sel_elem, Selection)
            selections[sel.name] = sel
        network = cls(name=element.attrib["name"], populations=populations,
                      projections=projections, selections=selections)
        return network

# can't "from ninem.user_layer.population import *" because of circular imports
from .population import Population, Selection
from .projection import Projection
