from copy import copy
from collections import defaultdict
from nineml.xml import E, NINEML, extract_xmlns, strip_xmlns
from nineml.base import DocumentLevelObject
from itertools import chain


class Annotations(defaultdict, DocumentLevelObject):
    """
    Defines the dimension used for quantity units
    """
    # FIXME: Annotations class needs a lot of work, will probably implement
    #        generic reader/writer to nested basic name=value pairs, which
    #        will be applied to 9ML namespaced annotations and can be
    #        associated with other namespacees through kwargs. Annotation
    #        namespaces with more involved loaders could provide them through
    #        kwargs also. TGC 11/15

    element_name = 'Annotations'

    @classmethod
    def _dict_tree(cls):
        return defaultdict(cls._dict_tree)

    def __init__(self, *args, **kwargs):
        # Create an infinite (on request) tree of defaultdicts
        super(Annotations, self).__init__(self._dict_tree, *args, **kwargs)

    # FIXME: Disabled Annotations deepcopy because it was causing problems.
    #        Need to rework the annotations so that it doesn't use nested
    #        defaultdicts (not a very good idea)
    def __deepcopy__(self, memo):  # @UnusedVariable
        return Annotations()

    def __repr__(self):
        return ("Annotations({})"
                .format(', '.join('{}={}'.format(k, v)
                                  for k, v in self.iteritems())))

    def to_xml(self, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 *chain(*[[E(k, str(v)) for k, v in dct.iteritems()]
                          for dct in self.itervalues()]))

    @classmethod
    def from_xml(cls, element):
        children = {}
        for child in element.getchildren():
            children[strip_xmlns(child.tag)] = child.text
        kwargs = {NINEML: children}
        return cls(**kwargs)


def read_annotations(from_xml):
    def annotate_from_xml(cls, element, *args, **kwargs):
        nineml_xmlns = extract_xmlns(element.tag)
        annot_elem = expect_none_or_single(
            element.findall(nineml_xmlns + Annotations.element_name))
        if annot_elem is not None:
            # Extract the annotations
            annotations = Annotations.from_xml(annot_elem)
            # Get a copy of the element with the annotations stripped
            element = copy(element)
            element.remove(element.find(nineml_xmlns +
                                        Annotations.element_name))
        else:
            annotations = Annotations()
        if (cls.__class__.__name__ == 'DynamicsXMLLoader' and
                VALIDATE_DIMENSIONS in annotations[nineml_xmlns]):
            # FIXME: Hack until I work out the best way to let other 9ML
            #        objects ignore this kwarg TGC 6/15
            kwargs['validate_dimensions'] = (
                annotations[nineml_xmlns][VALIDATE_DIMENSIONS] == 'True')
        nineml_object = from_xml(cls, element, *args, **kwargs)
        nineml_object.annotations.update(annotations.iteritems())
        return nineml_object
    return annotate_from_xml


def annotate_xml(to_xml):
    def annotate_to_xml(self, document_or_obj, **kwargs):
        # If Abstraction Layer class
        if hasattr(self, 'document'):
            obj = document_or_obj
        # If User Layer class
        else:
            obj = self
        elem = to_xml(self, document_or_obj, **kwargs)
        if obj.annotations:
            elem.append(obj.annotations.to_xml(**kwargs))
        return elem
    return annotate_to_xml


VALIDATE_DIMENSIONS = 'ValidateDimensions'

from nineml.utils import expect_none_or_single
