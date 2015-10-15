from itertools import chain
from .population import Population
from .projection import Projection
from .selection import Selection
from ..document import Document
from . import BaseULObject
from .component import write_reference, resolve_reference
from nineml.annotations import annotate_xml, read_annotations
from nineml.xmlns import E, NINEML
from nineml.base import DocumentLevelObject
import nineml
from nineml.exceptions import handle_xml_exceptions, NineMLRuntimeError


class Network(BaseULObject, DocumentLevelObject):
    """
    Container for populations and projections between those populations.

    **Arguments**:
        *name*
            a name for the network.
        *populations*
            a dict containing the populations contained in the network.
        *projections*
            a dict containing the projections contained in the network.
        *selections*
            a dict containing the selections contained in the network.
    """
    element_name = "Network"
    defining_attributes = ("populations", "projections", "selections")
    children = ("populations", "projections", "selections")

    def __init__(self, name="anonymous", populations={}, projections={},
                 selections={}):
        # better would be *items, then sort by type, taking the name from the
        # item
        super(Network, self).__init__()
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

    @property
    def elements(self):
        return chain(self.populations.itervalues(),
                     self.projections.itervalues(),
                     self.selections.itervalues())

    def get_components(self):
        components = []
        for p in chain(self.populations.values(), self.projections.values()):
            components.extend(p.get_components())
        return components

    @write_reference
    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 name=self.name,
                 *[p.to_xml(document, **kwargs) for p in chain(self.populations.values(),
                                             self.selections.values(),
                                             self.projections.values())])

    @classmethod
    @resolve_reference
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable @IgnorePep8
        cls.check_tag(element)
        populations = {}
        for pop_elem in element.findall(NINEML + 'Population'):
            pop = Population.from_xml(pop_elem, document)
            populations[pop.name] = pop
        projections = {}
        for proj_elem in element.findall(NINEML + 'Projection'):
            proj = Projection.from_xml(proj_elem, document)
            projections[proj.name] = proj
        selections = {}
        for sel_elem in element.findall(NINEML + 'Selection'):
            sel = Selection.from_xml(sel_elem, document)
            selections[sel.name] = sel
        network = cls(name=element.attrib["name"], populations=populations,
                      projections=projections, selections=selections)
        return network

    def write(self, filename):
        document = Document(*chain(
            self.populations.itervalues(), self.projections.itervalues(),
            self.selections.itervalues()))
        document.write(filename)

    @classmethod
    def read(self, filename):
        if isinstance(filename, basestring):
            document = nineml.read(filename)
        elif isinstance(filename, Document):
            document = filename
        else:
            raise NineMLRuntimeError(
                "Unrecognised argument type {}, can be either filename or "
                "Document".format(filename))
        return Network(
            name='root',
            populations=dict((p.name, p) for p in document.populations),
            projections=dict((p.name, p) for p in document.projections),
            selections=dict((s.name, s) for s in document.selections))
