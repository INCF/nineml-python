from copy import copy
from collections import defaultdict
from itertools import chain
from nineml.xml import E, extract_xmlns, strip_xmlns
from nineml.base import DocumentLevelObject, BaseNineMLObject, ContainerObject
import re
from nineml.xml import ElementMaker, nineml_ns, etree
from nineml.exceptions import (
    NineMLXMLError, NineMLRuntimeError, NineMLNameError)


def read_annotations(from_xml):
    def annotate_from_xml(cls, element, *args, **kwargs):
        nineml_xmlns = extract_xmlns(element.tag)
        annot_elem = expect_none_or_single(
            element.findall(nineml_xmlns + Annotations.nineml_type))
        if annot_elem is not None:
            # Extract the annotations
            annotations = Annotations.from_xml(annot_elem, **kwargs)
            # Get a copy of the element with the annotations stripped
            element = copy(element)
            element.remove(element.find(nineml_xmlns +
                                        Annotations.nineml_type))
        else:
            annotations = Annotations()
        if cls.__class__.__name__ == 'DynamicsXMLLoader':
            # FIXME: Hack until I work out the best way to let other 9ML
            #        objects ignore this kwarg TGC 6/15
            valid_dims = annotations.get(
                (VALIDATION, PY9ML_NS), DIMENSIONALITY,
                default='True') == 'True'
            kwargs['validate_dimensions'] = valid_dims
        nineml_object = from_xml(cls, element, *args, **kwargs)
        # Extract saved indices from annotations and save them in container
        # object.
        if (INDEX_TAG, PY9ML_NS) in annotations:
            for ind in annotations.pop((INDEX_TAG, PY9ML_NS)):
                key = ind.get(INDEX_KEY_ATTR)
                name = ind.get(INDEX_NAME_ATTR)
                index = ind.get(INDEX_INDEX_ATTR)
                nineml_object._indices[
                    key][getattr(nineml_object, key)(name)] = int(index)
        # Set extracted annotations in nineml_object
        nineml_object._annotations = annotations
        return nineml_object
    return annotate_from_xml


def annotate_xml(to_xml):
    def annotate_to_xml(self, document_or_obj, E=E, **kwargs):
        """
        Parameters
        ----------
        save_indices : bool
            Whether to save the indices assigned to sub-elements or not
        """
        # If Abstraction Layer class
        if xml_visitor_module_re.match(type(self).__module__):
            obj = document_or_obj
            options = self.options
        # If User Layer class
        else:
            obj = self
            options = kwargs
        xml = to_xml(self, document_or_obj, E=E, **kwargs)
        annot_xml = None
        if not options.get('no_annotations', False):
            if obj.annotations:
                annot_xml = obj.annotations.to_xml(E=E, **kwargs)
            # Append sub-element indices if 'save_indices' is provided and true
            if (options.get('save_indices', False) and
                    isinstance(obj, ContainerObject)):
                # Create empty annot_elem if container element doesn't have any
                # other annotations
                indices_annot = Annotations()
                for key, elem, index in obj.all_indices():
                    index_annot = indices_annot.add((INDEX_TAG, PY9ML_NS))
                    index_annot.set(INDEX_KEY_ATTR, key)
                    index_annot.set(INDEX_NAME_ATTR, elem.name)
                    index_annot.set(INDEX_INDEX_ATTR, index)
                ind_annot_xml = indices_annot.to_xml(E=E, **kwargs)
                if annot_xml is None:
                    annot_xml = ind_annot_xml
                else:
                    for child in ind_annot_xml.getchildren():
                        annot_xml.append(child)
        if annot_xml is not None:
            xml.append(annot_xml)
        return xml
    return annotate_to_xml


class BaseAnnotations(BaseNineMLObject):

    def __init__(self, branches=None):
        if branches is None:
            branches = defaultdict(list)
        self._branches = branches

    def __len__(self):
        return len(self._branches)

    def __repr__(self):
        return self._repr()

    def equals(self, other, **kwargs):  # @UnusedVariable
        try:
            if self.nineml_type != other.nineml_type:
                return False
        except AttributeError:
            return False
        return self._branches == other._branches

    def __iter__(self):
        return self._branches.iterkeys()

    def __contains__(self, key):
        return self._parse_key(key) in self._branches

    def __getitem__(self, key):
        """
        Returns the list of sub-branches for the given key

        Parameters
        ----------
        key : str
            The name of the annotations branch(es) to return
        """
        key = self._parse_key(key)
        if key in self._branches:
            key_branches = self._branches[key]
        else:
            raise NineMLNameError(
                "{} annotations branch does not have branch or attribute '{}'"
                .format(self._name, key))
        return key_branches

    def add(self, key, *args):
        """
        Adds a new branch for the given key. If the key exists already then
        then an additional branch is appended for that key.

        Parameters
        ----------
        key : str
            The name of the key to append a new branch for if no args provided
            otherwise the name of the branch to add a sub-branch to
        *args : list(str)
            A list of keys for the sub-branches ending in the key of the new
            sub-branch to add. Intermediate branches that are not present are
            added implicitly.
        """
        key = self._parse_key(key)
        key_branches = self._branches[key]
        if not key_branches or not args:
            branch = _AnnotationsBranch(*key)
            key_branches.append(branch)
        if args:
            if len(key_branches) > 1:
                raise NineMLNameError(
                    "Multiple branches found for key '{}' in annoations branch"
                    " '{}', cannot use 'add' method to add a sub-branch"
                    .format(key, self._name))
            branch = key_branches[0]
            branch.add(*args)
        return branch

    def pop(self, key):
        """
        Pops the list of sub-branches matching the given key

        Parameters
        ----------
        key : str | (str, str)
            A string containing the name of the branch to pop from the list or
            a tuple containing the name and namespace of the branch. If the
            namespace is not provided it is assumed to be the same as the
            branch above
        """
        try:
            return self._branches.pop(self._parse_key(key))
        except KeyError:
            return []

    def set(self, key, *args):
        """
        Sets the attribute of an annotations "leaf", creating intermediate
        branches if required

        Parameters
        ----------
        key : str
            Name of the first branch in the annotations tree
        *args : list(str) + (int|float|str)
            A list of subsequent branches to the leaf node followed by the
            attribute name and a value
        """
        key = self._parse_key(key)
        # Recurse into branches while there are remaining args
        key_branches = self._branches[key]
        if len(key_branches) == 1:
            branch = key_branches[0]
        elif not key_branches:
            branch = _AnnotationsBranch(*key)
            key_branches.append(branch)
        else:
            raise NineMLNameError(
                "Multiple branches found for key '{}' in annoations branch"
                " '{}', cannot use 'set' method".format(
                    key, self._name))
        branch.set(*args)  # recurse into branch

    def get(self, key, *args, **kwargs):
        """
        Gets the attribute of an annotations "leaf"

        Parameters
        ----------
        key : str
            Name of the first branch in the annotations tree
        *args : list(str) + (int|float|str)
            A list of subsequent branches to the leaf node followed by the
            attribute name to return the value of
        default: (int|float|str)
            The default value to return if the specified annotation has not
            been set

        Returns
        -------
        val : (int|float|str)
            The value of the annotation attribute
        """
        key = self._parse_key(key)
        if key in self._branches:
            key_branches = self._branches[key]
            if len(key_branches) == 1:
                # Recurse into branches while there are remaining args
                val = key_branches[0].get(*args, **kwargs)
            else:
                raise NineMLNameError(
                    "Multiple branches found for key '{}' in annoations "
                    "branch '{}', cannot use 'get' method".format(
                        key, self._name))
        else:
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise NineMLNameError(
                    "No annotation at path '{}'".format("', '".join(args)))
        return val

    @classmethod
    def _extract_key(cls, child):
        ns = extract_xmlns(child.tag)
        if not ns:
            raise NineMLXMLError(
                "All annotations must have a namespace: {}".format(
                    etree.tostring(child, pretty_print=True)))
        ns = ns[1:-1]  # strip braces
        name = strip_xmlns(child.tag)
        return (name, ns)

    def _sub_branches_to_xml(self, **kwargs):
        members = []
        for key_branches in self._branches.itervalues():
            for branch in key_branches:
                members.append(branch.to_xml(**kwargs))
        return members

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)


class Annotations(BaseAnnotations, DocumentLevelObject):
    """
    Is able to handle a basic hierarchical annotations format where the first
    level is the namespace of each sub element in the Annotations block
    """

    nineml_type = 'Annotations'
    defining_attributes = ('_branches',)

    def __init__(self, document=None):
        BaseAnnotations.__init__(self)
        DocumentLevelObject.__init__(self, document)

    def __repr__(self):
        rep = "Annotations:"
        for key_branch in self._branches.itervalues():
            for b in key_branch:
                rep += '\n' + b._repr(indent='  ')
        return rep

    def to_xml(self, E=E, **kwargs):  # @UnusedVariable
        return E(self.nineml_type, *self._sub_branches_to_xml(**kwargs))

    @classmethod
    def from_xml(cls, element, **kwargs):  # @UnusedVariable @IgnorePep8
        assert strip_xmlns(element.tag) == cls.nineml_type
        assert not element.attrib
        if element.text is not None:
            assert not element.text.strip()
        annot = cls(**kwargs)
        for child in element.getchildren():
            annot._branches[cls._extract_key(child)].append(
                _AnnotationsBranch.from_xml(child))
        return annot

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)
        clone._document = None

    def _parse_key(self, key):
        """
        Prepend current enclosing NS onto key if not provided explicitly

        Parameters
        ----------
        key : str
            Key of the annotations sub-branch
        """
        if not isinstance(key, tuple):
            raise NineMLXMLError(
                "All annotations under the root must have an explicit, "
                "'{}' branch does not".format(key))
        return key

    @property
    def _name(self):
        return 'Root'


class _AnnotationsBranch(BaseAnnotations):

    nineml_type = '_AnnotationsBranch'
    defining_attributes = ('_branches', '_attr', '_name', '_ns', '_text')

    def __init__(self, name, ns, attr=None, branches=None, text=None):
        super(_AnnotationsBranch, self).__init__(branches)
        if attr is None:
            attr = {}
        self._name = name
        self._ns = ns
        self._attr = attr
        self._text = text

    @property
    def name(self):
        return self._name

    @property
    def ns(self):
        return self._ns

    @property
    def text(self):
        return self._text

    @property
    def attr(self):
        return self._attr

    def equals(self, other, **kwargs):  # @UnusedVariable
        return (super(_AnnotationsBranch, self).equals(other) and
                self.name == other.name and
                self.attr == other.attr and
                self.text == other.text and
                self.ns == other.ns)

    def _repr(self, indent=''):
        rep = "{}{{{}}}{}:".format(indent, self.ns, self.name)
        for attr, val in self.attr_items():
            rep += '\n{}{}={}'.format(indent + '  ', attr, val)
        for key_branches in self._branches.itervalues():
            for branch in key_branches:
                rep += '\n' + branch._repr(indent=indent + '  ')
        if self.text is not None:
            rep += '\n{}__text__={}'.format(indent + '  ', self.text)
        return rep

    def attr_values(self):
        return self._attr.itervalues()

    def attr_keys(self):
        return self._attr.iterkeys()

    def attr_items(self):
        return self._attr.iteritems()

    def set(self, key, *args):
        """
        Sets the attribute of an annotations "leaf", creating intermediate
        branches if required

        Parameters
        ----------
        key : str
            Name of the first branch in the annotations tree
        *args : list(str) + (int|float|str)
            A list of subsequent branches to the leaf node followed by the
            attribute name and a value
        """
        if len(args) == 1:
            self._attr[key] = str(args[0])
        elif not args:
            raise NineMLRuntimeError("No value was provided to set of '{}' "
                                     "in annotations branch '{}'"
                                     .format(key, self.name))
        else:
            super(_AnnotationsBranch, self).set(key, *args)

    def get(self, key, *args, **kwargs):
        """
        Gets the attribute of an annotations "leaf"

        Parameters
        ----------
        key : str
            Name of the first branch in the annotations tree
        *args : list(str) + (int|float|str)
            A list of subsequent branches to the leaf node followed by the
            attribute name to return the value of
        default: (int|float|str)
            The default value to return if the specified annotation has not
            been set

        Returns
        -------
        val : (int|float|str)
            The value of the annotation attribute
        """
        if not args:
            if 'default' in kwargs:
                val = self._attr.get(key, kwargs['default'])
            else:
                val = self._attr[key]
        else:
            val = super(_AnnotationsBranch, self).get(key, *args, **kwargs)
        return val

    def to_xml(self, **kwargs):  # @UnusedVariable
        E = ElementMaker(namespace=self.ns)
        members = self._sub_branches_to_xml(**kwargs)
        if self.text is not None:
            members.append(self.text)
        return E(self.name, *members, **self._attr)

    @classmethod
    def from_xml(cls, element, **kwargs):  # @UnusedVariable
        name, ns = cls._extract_key(element)
        branches = defaultdict(list)
        for child in element.getchildren():
            branches[cls._extract_key(child)].append(
                _AnnotationsBranch.from_xml(child))
        attr = dict(element.attrib)
        if element.text is not None and element.text.strip():
            text = element.text.strip()
        else:
            text = None
        return cls(name, ns, attr=attr, branches=branches, text=text)

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)

    def _parse_key(self, key):
        """
        Prepend current enclosing NS onto key if not provided explicitly

        Parameters
        ----------
        key : str
            Key of the annotations sub-branch
        """
        if not isinstance(key, tuple):
            key = (key, self.ns)
        return key


# Python-9ML library specific annotations
PY9ML_NS = 'http://github.com/INCF/lib9ml'

# Annotation
INDICES_TAG = 'Indices'
INDEX_TAG = 'Index'
INDEX_KEY_ATTR = 'key'
INDEX_NAME_ATTR = 'name'
INDEX_INDEX_ATTR = 'index'

# Dimension validation
VALIDATION = 'Validation'
DIMENSIONALITY = 'dimensionality'


xml_visitor_module_re = re.compile(r'nineml\.abstraction\.\w+\.visitors\.xml')


from nineml.utils import expect_none_or_single  # @IgnorePep8
