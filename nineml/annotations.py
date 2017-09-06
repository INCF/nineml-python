from nineml.utils import OrderedDefaultListDict
from nineml.base import DocumentLevelObject, BaseNineMLObject
import re
from nineml.exceptions import (
    NineMLXMLError, NineMLRuntimeError, NineMLNameError)


class BaseAnnotations(BaseNineMLObject):

    def __init__(self, branches=None):
        self._branches = OrderedDefaultListDict()
        if branches is not None:
            assert all(isinstance(b, list) for b in branches.itervalues())
            self._branches.update(branches)

    def __len__(self):
        return len(self._branches)

    def __repr__(self):
        return self._repr()

    @property
    def branches(self):
        return self._branches

    def empty(self):
        """
        Returns true if there are no annotation branches.
        """
        return not self._branches

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

    def delete(self, key, *args, **kwargs):
        """
        Gets the attribute of an annotations "leaf"

        Parameters
        ----------
        key : str
            Name of the first branch in the annotations tree
        *args : list(str) + (int|float|str)
            A list of subsequent branches to the leaf node followed by the
            attribute name to delete
        """
        key = self._parse_key(key)
        if key in self._branches:
            key_branches = self._branches[key]
            if len(key_branches) == 1:
                # Recurse into branches while there are remaining args
                key_branches[0].delete(*args, **kwargs)
                if key_branches[0].empty():
                    del self._branches[key]
            else:
                raise NineMLNameError(
                    "Multiple branches found for key '{}' in annoations "
                    "branch '{}', cannot use 'delete' method".format(
                        key, self._name))

    def _sub_branches_serialize(self, **kwargs):
        members = []
        for key_branches in self._branches.itervalues():
            for branch in key_branches:
                members.append(branch.serialize(**kwargs))
        return members

    def serialize_node(self, node, **options):  # @UnusedVariable
        for (name, ns), key_branches in self._branches.iteritems():
            for branch in key_branches:
                branch_elem = node.visitor.create_elem(
                    name, parent=node.serial_element, multiple=True,
                    namespace=ns, **options)
                branch_node = type(node)(node.visitor, branch_elem)
                branch.serialize_node(branch_node, **options)

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)


class Annotations(BaseAnnotations, DocumentLevelObject):
    """
    Is able to handle a basic hierarchical annotations format where the first
    level is the namespace of each sub element in the Annotations block
    """

    nineml_type = 'Annotations'
    defining_attributes = ('_branches',)

    def __init__(self, branches=None):
        BaseAnnotations.__init__(self, branches=branches)
        DocumentLevelObject.__init__(self)

    def __repr__(self):
        rep = "Annotations:"
        for key_branch in self._branches.itervalues():
            for b in key_branch:
                rep += '\n' + b._repr(indent='  ')
        return rep

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable @IgnorePep8
        branches = OrderedDefaultListDict()
        for name, elem in node.visitor.get_all_children(node.serial_element):
            ns = node.visitor.get_namespace(elem)
            child_node = type(node)(node.visitor, elem, name, **options)
            branches[(name, ns)].append(_AnnotationsBranch.unserialize_node(
                child_node, name, ns, **options))
        return cls(branches)

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

    @classmethod
    def unserialize(cls, serial_elem, format, version,  # @ReservedAssignment @IgnorePep8
                    **kwargs):
        kwargs.pop('check_unprocessed', False)
        return nineml.unserialize(serial_elem, cls, format=format,
                                  version=version, check_unprocessed=False,
                                  **kwargs)


class _AnnotationsBranch(BaseAnnotations):

    nineml_type = '_AnnotationsBranch'
    defining_attributes = ('_branches', '_attr', '_name', '_ns', '_body')
    nineml_attr = ('attr', 'name', 'ns', 'body')

    def __init__(self, name, ns, attr=None, branches=None, body=None):
        super(_AnnotationsBranch, self).__init__(branches)
        if attr is None:
            attr = {}
        self._name = name
        self._ns = ns
        self._attr = attr
        self._body = body

    def empty(self):
        return super(_AnnotationsBranch, self).empty() and not self.attr

    @property
    def name(self):
        return self._name

    @property
    def ns(self):
        return self._ns

    @property
    def body(self):
        return self._body

    @property
    def attr(self):
        return self._attr

    def equals(self, other, **kwargs):  # @UnusedVariable
        return (super(_AnnotationsBranch, self).equals(other) and
                self.name == other.name and
                self.attr == other.attr and
                self.body == other.body and
                self.ns == other.ns)

    def _repr(self, indent=''):
        rep = "{}{{{}}}{}:".format(indent, self.ns, self.name)
        for attr, val in self.attr_items():
            rep += '\n{}{}={}'.format(indent + '  ', attr, val)
        for key_branches in self._branches.itervalues():
            for branch in key_branches:
                rep += '\n' + branch._repr(indent=indent + '  ')
        if self.body is not None:
            rep += '\n{}__body__={}'.format(indent + '  ', self.body)
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
                try:
                    val = self._attr[key]
                except KeyError:
                    raise NineMLNameError(
                        "Annotations branch {{{}}}{} does not contain '{}' "
                        "attribute".format(self.ns, self.name, key))
        else:
            val = super(_AnnotationsBranch, self).get(key, *args, **kwargs)
        return val

    def delete(self, key, *args, **kwargs):
        """
        Gets the attribute of an annotations "leaf"

        Parameters
        ----------
        key : str
            Name of the first branch in the annotations tree
        *args : list(str) + (int|float|str)
            A list of subsequent branches to the leaf node followed by the
            attribute name to delete
        """
        if not args:
            try:
                del self.attr[key]
            except KeyError:
                raise NineMLNameError(
                    "Annotations branch {{{}}}{} does not contain '{}' "
                    "attribute".format(self.ns, self.name, key))
        else:
            super(_AnnotationsBranch, self).delete(key, *args, **kwargs)

    def serialize_node(self, node, **options):  # @UnusedVariable
        super(_AnnotationsBranch, self).serialize_node(node, **options)
        if self.body is not None:
            node.body(self.body)
        for key, val in self._attr.iteritems():
            node.attr(key, val)

    @classmethod
    def unserialize_node(cls, node, name, ns, **options):  # @UnusedVariable @IgnorePep8
        branches = OrderedDefaultListDict()
        for child_name, child_elem in node.visitor.get_all_children(
                node.serial_element):
            child_ns = node.visitor.get_namespace(child_elem)
            child_node = type(node)(node.visitor, child_elem, child_name,
                                    check_unprocessed=False)
            branches[(child_name, child_ns)].append(
                cls.unserialize_node(child_node, child_name, child_ns,
                                     **options))
        attr = dict((k, node.attr(k))
                    for k in node.visitor.get_attr_keys(node.serial_element))
        return cls(name, ns, attr=attr, branches=branches,
                   body=node.body(allow_empty=True))

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
PY9ML_NS = 'http://github.com/INCF/nineml-python'

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

import nineml  # @IgnorePep8
