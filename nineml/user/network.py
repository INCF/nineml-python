from itertools import chain
from .population import Population
from .projection import Projection
from .selection import Selection
from ..document import Document
from copy import copy
from . import BaseULObject
from .component import write_reference, resolve_reference
from nineml.annotations import annotate_xml, read_annotations
from nineml.xml import E, get_xml_attr
from nineml.base import DocumentLevelObject
from nineml.xml import from_child_xml, unprocessed_xml, get_xml_attr
import nineml
from nineml.exceptions import NineMLRuntimeError


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
    defining_attributes = ("_populations", "_projections", "_selections")

    def __init__(self, name="anonymous", populations=[], projections=[],
                 selections=[], document=None):
        # better would be *items, then sort by type, taking the name from the
        # item
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document=document)
        self.name = name
        self._populations = dict((p.name, p) for p in populations)
        self._projections = dict((p.name, p) for p in projections)
        self._selections = dict((s.name, s) for s in selections)

    @property
    def populations(self):
        return self._populations.itervalues()

    @property
    def projections(self):
        return self._projections.itervalues()

    @property
    def selections(self):
        return self._selections.itervalues()

    def add(self, *objs):
        """
        Add one or more Population, Projection or Selection instances to the
        network.
        """
        for obj in objs:
            if isinstance(obj, Population):
                self._populations[obj.name] = obj
            elif isinstance(obj, Projection):
                self._projections[obj.name] = obj
            elif isinstance(obj, Selection):
                self._selections[obj.name] = obj
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
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        as_ref_kwargs = copy(kwargs)
        as_ref_kwargs['as_reference'] = True
        member_elems = []
        for member in chain(self.populations, self.selections,
                            self.projections):
#             member.set_local_reference(document, overwrite=False)
            member_elems.append(member.to_xml(document, **as_ref_kwargs))
        return E(self.element_name, name=self.name, *member_elems)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        populations = from_child_xml(element, Population, document,
                                     multiple=True, allow_reference='only',
                                     allow_none=True, **kwargs)
        projections = from_child_xml(element, Projection, document,
                                     multiple=True, allow_reference='only',
                                     allow_none=True, **kwargs)
        selections = from_child_xml(element, Selection, document,
                                     multiple=True, allow_reference='only',
                                     allow_none=True, **kwargs)
        network = cls(name=get_xml_attr(element, 'name', document, **kwargs), populations=populations,
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
