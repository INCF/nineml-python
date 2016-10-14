from copy import copy
from nineml.xml import E, extract_xmlns, strip_xmlns
from nineml.base import DocumentLevelObject, BaseNineMLObject
import re
from nineml.xml import ElementMaker, nineml_ns, etree
from nineml.exceptions import NineMLXMLError, NineMLRuntimeError


def read_annotations(from_xml):
    def annotate_from_xml(cls, element, *args, **kwargs):
        nineml_xmlns = extract_xmlns(element.tag)
        annot_elem = expect_none_or_single(
            element.findall(nineml_xmlns + Annotations.nineml_type))
        if annot_elem is not None:
            # Extract the annotations
            annotations = Annotations.from_xml(annot_elem)
            # Get a copy of the element with the annotations stripped
            element = copy(element)
            element.remove(element.find(nineml_xmlns +
                                        Annotations.nineml_type))
        else:
            annotations = Annotations()
        if (cls.__class__.__name__ == 'DynamicsXMLLoader' and
                VALIDATE_DIMENSIONS in annotations[nineml_xmlns]):
            # FIXME: Hack until I work out the best way to let other 9ML
            #        objects ignore this kwarg TGC 6/15
            kwargs['validate_dimensions'] = (
                annotations[nineml_xmlns][VALIDATE_DIMENSIONS] == 'True')
        nineml_object = from_xml(cls, element, *args, **kwargs)
        nineml_object._annotations = annotations
        return nineml_object
    return annotate_from_xml


def annotate_xml(to_xml):
    def annotate_to_xml(self, document_or_obj, **kwargs):
        # If Abstraction Layer class
        if xml_visitor_module_re.match(type(self).__module__):
            obj = document_or_obj
            options = self.options
        # If User Layer class
        else:
            obj = self
            options = kwargs
        elem = to_xml(self, document_or_obj, **kwargs)
        if (not options.get('no_annotations', False) and
                any(a for a in obj.annotations.itervalues())):
            elem.append(obj.annotations.to_xml(**kwargs))
        return elem
    return annotate_to_xml


class Annotations(DocumentLevelObject):
    """
    Is able to handle a basic hierarchical annotations format where the first
    level is the namespace of each sub element in the Annotations block
    """

    nineml_type = 'Annotations'
    defining_attributes = ('_namespaces',)

    def __init__(self, document=None):
        super(Annotations, self).__init__(document)
        self._namespaces = {}

    def __repr__(self):
        return "Annotations:\n{}".format(
            "\n".join(str(v) for v in self._namespaces.itervalues()))

    def __getitem__(self, key):
        try:
            val = self._namespaces[key]
        except KeyError:
            val = self._namespaces[key] = _AnnotationsNamespace(key)
        return val

    def to_xml(self, **kwargs):  # @UnusedVariable
        members = []
        for ns, branch in self._namespaces.iteritems():
            if isinstance(branch, _AnnotationsBranch):
                for sub_branch in branch.branches:
                    members.append(sub_branch.to_xml(ns=ns, **kwargs))
            else:
                assert isinstance(branch, _AnnotationsNamespace)
                members.append(branch)  # Append unprocessed XML
        return E(self.nineml_type, *members)

    @classmethod
    def from_xml(cls, element, read_annotation_ns=None, **kwargs):  # @UnusedVariable @IgnorePep8
        if read_annotation_ns is None:
            read_annotation_ns = []
        elif isinstance(read_annotation_ns, basestring):
            read_annotation_ns = [read_annotation_ns]
        assert strip_xmlns(element.tag) == cls.nineml_type
        annot = cls(**kwargs)
        for child in element.getchildren():
            ns = extract_xmlns(child.tag)
            if not ns:
                raise NineMLXMLError(
                    "All annotations must have a namespace: {}".format(
                        etree.tostring(child, pretty_print=True)))
            ns = ns[1:-1]  # strip braces
            if ns == nineml_ns or ns in read_annotation_ns:
                name = strip_xmlns(child.tag)
                annot[ns][name] = _AnnotationsBranch.from_xml(child)
            else:
                annot._namespaces[ns] = child  # Don't process, just ignore
        return annot

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)
        clone._document = self._document


class _AnnotationsNamespace(dict):
    """
    Like a defaultdict, but initialises AnnotationsBranch with a name
    """

    def __init__(self, ns):
        self._ns = ns

    @property
    def ns(self):
        return self._ns

    def __repr__(self):
        rep = '"{}":\n'.format(self.ns)
        rep += '\n'.join(v._repr('  ') for v in self.itervalues())
        return rep

    def __getitem__(self, key):
        try:
            val = super(_AnnotationsNamespace, self).__getitem__(key)
        except KeyError:
            val = self[key] = _AnnotationsBranch(key)
        return val

    def __setitem__(self, key, val):
        if not isinstance(val, _AnnotationsBranch):
            raise NineMLRuntimeError(
                "Attempting to set directly to Annotations namespace '{}' "
                "(key={}, val={})".format(self.name, key, val))
        super(_AnnotationsNamespace, self).__setitem__(key, val)


class _AnnotationsBranch(BaseNineMLObject):

    nineml_type = '_AnnotationsBranch'
    defining_attributes = ('_branches', '_attr')

    def __init__(self, name, attr=None, branches=None):
        if attr is None:
            attr = {}
        if branches is None:
            branches = {}
        self._branches = branches
        self._name = name
        self._attr = attr

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return self._repr()

    def _repr(self, indent=''):
        rep = "{}{}:".format(indent, self.name)
        if self._attr:
            rep += '\n' + '\n'.join('{}{}={}'.format(indent + '  ', *i)
                                    for i in self._attr.iteritems())
        if self._branches:
            rep += '\n' + '\n'.join(b._repr(indent=indent + '  ')
                                    for b in self._branches.itervalues())
        return rep

    def __iter__(self):
        return self.keys()

    def values(self):
        return self._attr.itervalues()

    def keys(self):
        return self._attr.iterkeys()

    def items(self):
        return self._attr.iteritems()

    @property
    def branches(self):
        return self._branches.itervalues()

    def __getitem__(self, key):
        try:
            val = self._branches[key]
        except KeyError:
            # Create a new annotations branch next level of annotations
            val = self._branches[key] = _AnnotationsBranch(key)
        return val

    def get(self, key, default=None):
        """Like getitem but doesn't create a new branch if one isn't present"""
        try:
            val = self._attr[key]
        except KeyError:
            val = default
        return val

    def __setitem__(self, key, val):
        self._attr[key] = str(val)

    def to_xml(self, ns=None, **kwargs):  # @UnusedVariable
        if ns is None:
            ns = nineml_ns
        E = ElementMaker(namespace=ns, nsmap={None: ns})
        return E(self.name,
                 *(sb.to_xml(**kwargs) for sb in self._branches),
                 **self._attr)

    @classmethod
    def from_xml(cls, element, **kwargs):  # @UnusedVariable
        name = strip_xmlns(element.tag)
        branches = {}
        for child in element.getchildren():
            branches[
                strip_xmlns(child.tag)] = _AnnotationsBranch.from_xml(child)
        attr = dict(element.attrib)
        return cls(name, attr, branches)

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)


VALIDATE_DIMENSIONS = 'ValidateDimensions'

xml_visitor_module_re = re.compile(r'nineml\.abstraction\.\w+\.visitors\.xml')


from nineml.utils import expect_none_or_single  # @IgnorePep8
