# encoding: utf-8
"""
Python module for reading/writing any top level 9ml objects within a NineML
root tag.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from . import E, NINEML
from .utility import expect_single, expect_none_or_single
import itertools
import collections
import nineml.user_layer
import nineml.abstraction_layer
from .user_layer.components.base import Reference


class Context(dict):
    """
    Loads and stores all top-level elements in a NineML file (i.e. any element
    that is able to sit directly within <NineML>...</NineML> tags). All
    elements are stored initially but only converted to lib9ml objects on
    demand so it doesn't matter which order they appear in the NineML file.
    """

    element_name = 'NineML'

    ## Valid top-level NineML element names
    top_level_abstraction = ['Dimension', 'Unit', 'ComponentClass',
                             'Annotation']
    top_level_user = ['Component', 'PositionList',
                      'Population', 'Selection', 'Projection']

    # A tuple to hold the unresolved elements
    _Unloaded = collections.namedtuple('_Unloaded', 'name xml cls')

    def __init__(self, *args, **kwargs):
        self.url = kwargs.pop('_url', None)
        super(Context, self).__init__(*args, **kwargs)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []

    def resolve_ref(self, containing_elem, inline_type=None):
        """
        This method is used for resolving a member element that can either be
        defined in the current file (i.e. within a 'Reference' tag without a
        url attribute), in a separate file (i.e. within a 'Reference' tag with
        a url attribute) or inline (i.e. no 'Reference' tag just the object).

        `containing_elem` -- the XML element that contains the Reference or
                             inline object
        `inline_type`     -- the expected type of the object to be referenced.
                             This is used to check the referene points to the
                             correct object and also to convert inline objects.
                             If it is not provided in-line definitions are not
                             permitted.
        """
        elem = expect_none_or_single(
                      containing_elem.findall(NINEML + Reference.element_name))
        if elem is not None:
            ref = Reference.from_xml(elem, self)
            if inline_type and not isinstance(ref.user_layer_object,
                                              inline_type):
                raise TypeError("Type of referenced object ('{}') does not "
                                "match expected type ('{}')"
                                .format(ref.user_layer_object.__class__,
                                        inline_type))
            obj = ref.user_layer_object
        else:
            if not inline_type:
                raise Exception("This '{}' element does not permit inline "
                                "child elements".format(containing_elem.tag))
            elem = expect_single(containing_elem.findall(NINEML + 'Component'))
            obj = inline_type.from_xml(elem, self)
        return obj

    def __getitem__(self, name):
        """
        Returns the element referenced by the given name
        """
        try:
            elem = super(Context, self).__getitem__(name)
        except KeyError:
            # FIXME: Not sure if this is a good idea or not, it allows
            #        attributes to be omitted from XML tags for example
            if name is None:
                return None
            raise KeyError("'{}' was not found in the NineML context{} ("
                           "elements in the context were '{}')."
                           .format(name, self.url or '',
                                   "', '".join(self.iterkeys())))
        if isinstance(elem, self._Unloaded):
            elem = self._load_elem_from_xml(elem)
        return elem

    @property
    def components(self):
        return (self[k] for k in self.iterkeys()
                if isinstance(self[k], nineml.user_layer.Component))

    @property
    def component_classes(self):
        return (self[k] for k in self.iterkeys()
                if isinstance(self[k],
                              nineml.abstraction_layer.ComponentClass))

    def _load_elem_from_xml(self, unloaded):
        """
        Resolve an element from its XML description and store back in the
        element dictionary
        """
        if unloaded in self._loading:
            raise Exception("Circular reference detected in '{}(name={})' "
                            "element. Resolution stack was:\n"
                            .format(unloaded.name,
                                    "\n".join('{}(name={})'.format(u.tag,
                                                                   u.name)
                                              for u in self._loading)))
        self._loading.append(unloaded)
        elem = unloaded.cls.from_xml(unloaded.xml, self)
        assert self._loading[-1] is unloaded
        self._loading.pop()
        self[unloaded.name] = elem
        return elem

    def to_xml(self):
        return E(self.element_name,
                 *[c.to_xml() for c in self.itervalues()])

    @classmethod
    def from_xml(cls, element, url=None):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Not a NineML root ('{}')".format(element.tag))
        # Initialise the context
        elements = {'_url': url}
        # Loop through child elements, determine the class needed to extract
        # them and add them to the dictionary
        for child in element.getchildren():
            if child.tag in (NINEML + e for e in cls.top_level_user):
                child_cls = getattr(nineml.user_layer, child.tag[len(NINEML):])
            elif child.tag in (NINEML + e for e in cls.top_level_abstraction):
                child_cls = getattr(nineml.abstraction_layer,
                                    child.tag[len(NINEML):])
            else:
                top_level = itertools.chain(cls.top_level_abstraction,
                                            cls.top_level_user)
                raise Exception("Invalid top-level element '{}' found in "
                                "NineML document (valid elements are '{}')."
                                .format(child.tag, "', '".join(top_level)))
            if child.tag == NINEML + 'Annotation':
                elements['_annotation'] = child
            else:
                # Units use 'symbol' as their unique identifier (from LEMS) all
                # other elements use 'name'
                name = child.attrib.get('name', child.attrib.get('symbol'))
                if name in elements:
                    raise Exception("Conflicting identifiers '{ob1}:{name} in "
                                    "{ob2}:{name} in NineML file '{url}'"
                                    .format(
                                           name=name,
                                           ob1=elements[name].cls.element_name,
                                           ob2=child_cls.element_name,
                                           url=url or ''))
                elements[name] = cls._Unloaded(name, child, child_cls)
        return cls(**elements)
