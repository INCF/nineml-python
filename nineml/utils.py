"""
This module contains general purpose utility functions for simplifying list
analysis.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from os.path import dirname, normpath, realpath, exists, join
import os
import sys
import re
import math
import itertools
import hashlib
import collections
from .exceptions import internal_error
from .exceptions import NineMLRuntimeError, NineMLXMLBlockError
from .xmlns import extract_xmlns
from nineml.base import ContainerObject
from nineml.reference import Reference


def from_child_xml(element, child_classes, document, multiple=False,
                   allow_reference=False, allow_none=False, within=None,
                   unprocessed=set(), **kwargs):
    # Ensure child_classes is an iterable
    if isinstance(child_classes, type):
        child_classes = (child_classes,)
    assert child_classes, "No child classes supplied"
    # Get the namespace of the element (i.e. NineML version)
    xmlns = extract_xmlns(element.tag)
    # Get the name of the element for error messages if present
    try:
        elem_name = element.name + ' ' + element.element_name
    except AttributeError:
        elem_name = element.name
    # Get the parent element of the child elements to parse. For example the
    # in Projection elements where pre and post synaptic population references
    # are enclosed within 'Pre' or 'Post' tags respectively
    if within:
        within_elems = element.findall(xmlns + within)
        if len(within_elems) == 1:
            parent = within_elems[0]
        elif not within_elems:
            raise NineMLXMLBlockError(
                "Did not find {} block within {} element in '{}'"
                .format(within, elem_name, document.url))
        else:
            raise NineMLXMLBlockError(
                "Found unexpected multiple {} blocks within {} in '{}'"
                .format(within, elem_name, document.url))
    else:
        parent = element
    # Get the name of the parent and child classes for error messages
    try:
        parent_name = parent.name + ' ' + parent.element_name
    except AttributeError:
        parent_name = parent.element_name
    # Get the list of child class names for error messages
    child_cls_names = "', '".join(c.element_name for c in child_classes)
    # Append all child classes
    children = []
    if allow_reference != 'only':
        for child_cls in child_classes:
            for child_elem in parent.findall(xmlns + child_cls.element_name):
                children.append(child_cls.from_xml(child_elem, document,
                                                   **kwargs))
                unprocessed.discard(child_elem)
    if allow_reference:
        for ref_elem in parent.findall(xmlns + Reference.element_name):
            ref = Reference.from_xml(ref_elem, document, **kwargs)
            if isinstance(ref.user_object, child_classes):
                children.append(ref.user_object)
                unprocessed.discard(ref_elem)
    if not children:
        if allow_none:
            result = [] if multiple else None
        else:
            raise NineMLXMLBlockError(
                "Did not find and child blocks with the tag{s} "
                "'{child_cls_names}'in the {parent_name} in '{url}'"
                .format(child_cls_names=child_cls_names,
                        s=len(child_classes), parent_name=parent_name,
                        url=document.url))
    elif multiple:
        result = children
    elif len(children) == 1:
        result = children[0]  # Expect single
    else:
        raise NineMLXMLBlockError(
            "Multiple children of types '{}' found within {} in '{}'"
            .format(child_cls_names, parent_name, document.url))
    return result


def _dispatch_error_func(error_func, default_error=NineMLRuntimeError()):
    """Internal function for dispatching errors.

    This was seperated out because it happens in a lot of utility functions
    """

    if error_func:
        if isinstance(error_func, Exception):
            raise error_func
        elif isinstance(error_func, basestring):
            raise NineMLRuntimeError(error_func)
        else:
            error_func()
            internal_error('error_func failed to raise Exception')
    else:
        if isinstance(default_error, Exception):
            raise default_error
        elif isinstance(default_error, basestring):
            raise NineMLRuntimeError(default_error)
        else:
            default_error()
            internal_error('default_error failed to raise Exception')


def _is_iterable(obj):
    return hasattr(obj, '__iter__')


def _is_hashable(obj):
    try:
        hash(obj)
        return True
    except:
        return False


def expect_single(lst, error_func=None):
    """Retrieve a single element from an iterable.

    This function tests whether an iterable contains just a single element and
    if so returns that element. Otherwise it raises an Exception.

    :param lst: An iterable

    :param error_func: An exception object or a callable. ``error_func`` will
        be raised or called in case there is not exactly one element in
        ``lst``. If ``error_func`` is ``None``, a ``NineMLRuntimeError``
        exception will be raised.

    :rtype: the element in the list, ``lst[0]``, provided ``len(lst)==1``

    >>> expect_single( ['hello'] )
    'hello'

    >>> expect_single( [1] )
    1

    >>> expect_single( [] ) #doctest: +SKIP
    NineMLRuntimeError: expect_single() recieved an iterable of length: 0

    >>> expect_single( [None,None] ) #doctest: +SKIP
    NineMLRuntimeError: expect_single() recieved an iterable of length: 2

    >>> expect_single( [], lambda: raise_exception( RuntimeError('Aggh') ) #doctest: +SKIP  # @IgnorePep8
    RuntimeError: Aggh

    >>> #Slightly more tersly:
    >>> expect_single( [], RuntimeError('Aggh') ) #doctest: +SKIP
    RuntimeError: Aggh

    """

    if not _is_iterable(lst):
        raise NineMLRuntimeError('Object not iterable')
    if issubclass(lst.__class__, (dict)):
        err = "Dictionary passed to expect_single. This could be ambiguous"
        err += "\nIf this is what you intended, please explicity pass '.keys' "
        raise NineMLRuntimeError(err)

    lst = list(lst)

    # Good case:
    if len(lst) == 1:
        return lst[0]

    # Bad case: our list doesn't contain just one element
    errmsg = 'expect_single() recieved an iterable of length: %d' % len(lst)
    errmsg += '\n  - List Contents:' + str(lst) + '\n'
    _dispatch_error_func(error_func, NineMLRuntimeError(errmsg))


def expect_none_or_single(lst, error_func=None):
    """Retrieve a single element from an iterable.

    This function tests whether an iterable contains just a single element and
    if so returns that element. Otherwise it raises an Exception.

    :param lst: An iterable

    :param error_func: An exception object or a callable. ``error_func`` will
        be raised or called in case there is not exactly one element in
        ``lst``. If ``error_func`` is ``None``, a ``NineMLRuntimeError``
        exception will be raised.

    :rtype: the element in the list, ``lst[0]``, provided ``len(lst)==1``

    >>> expect_single( ['hello'] )
    'hello'

    >>> expect_single( [1] )
    1

    >>> expect_single( [] ) #doctest: +SKIP
    NineMLRuntimeError: expect_single() recieved an iterable of length: 0

    >>> expect_single( [None,None] ) #doctest: +SKIP
    NineMLRuntimeError: expect_single() recieved an iterable of length: 2

    >>> expect_single( [], lambda: raise_exception( RuntimeError('Aggh') ) #doctest: +SKIP
    RuntimeError: Aggh

    >>> #Slightly more tersly:
    >>> expect_single( [], RuntimeError('Aggh') ) #doctest: +SKIP
    RuntimeError: Aggh

    """

    if not _is_iterable(lst):
        raise NineMLRuntimeError('Object not iterable')
    if issubclass(lst.__class__, (dict)):
        err = "Dictionary passed to expect_single. This could be ambiguous"
        err += "\nIf this is what you intended, please explicity pass '.keys' "
        raise NineMLRuntimeError(err)

    lst = list(lst)

    # Good case:
    if len(lst) == 1:
        return lst[0]
    elif len(lst) == 0:
        return None
    else:
        # Bad case: our list doesn't contain just one element
        errmsg = ('expect_none_or_single() recieved an iterable of length: %d'
                  % len(lst))
        errmsg += '\n  - List Contents:' + str(lst) + '\n'
        _dispatch_error_func(error_func, NineMLRuntimeError(errmsg))


def _filter(lst, func=None):
    """Filter a list according to a predicate.

    Takes a sequence [o1,o2,..] and returns a list contains those which
    are not `None` and satisfy the predicate `func(o)`

    :param lst: Input iterable (not a dictionary)
    :param func: Predicate function. If ``none``, this function always returns
                 ``True``


    Implementation::

        if func:
            return  [ l for l in lst if l is not None and func(l) ]
        else:
            return  [ l for l in lst if l is not None]

    Examples:

    >>> _filter( ['hello','world'] )         #doctest: +NORMALIZE_WHITESPACE
    ['hello', 'world']


    >>> _filter( ['hello',None,'world'] )    #doctest: +NORMALIZE_WHITESPACE
    ['hello', 'world']

    >>> _filter( [None,] )                   #doctest: +NORMALIZE_WHITESPACE
    []

    """

    if func:
        return [l for l in lst if l is not None and func(l)]
    else:
        return [l for l in lst if l is not None]


def filter_expect_single(lst, func=None, error_func=None):
    """Find a single element matching a predicate in a list.

       This is a syntactic-sugar function ``_filter`` and ``expect_single``
       in a single call.

        Returns::

            expect_single( _filter(lst, func), error_func )


        This is useful when we want to find an item in a sequence with a
        certain property, and expect there to be only one.

        Examples:

        >>> find_smith = lambda s: s.split()[-1] == 'Smith'
        >>> filter_expect_single( ['John Smith','Tim Jones'], func=find_smith )  #doctest: +NORMALIZE_WHITESPACE
        'John Smith'

    """
    return expect_single(_filter(lst, func), error_func)


def filter_by_type(lst, acceptedtype):
    """ Find all the objects of a certain type in a list

        This is a syntactic sugar function, which returns a list of all the
        objects in a iterable for which  ``isinstance(o,acceptedtype) == True``
        and for which the objects are not ``None``. i.e::

            filter_by_type([None], types.NoneType)
            []

    """
    return _filter(lst, lambda x: isinstance(x, acceptedtype))


def filter_discrete_types(lst, acceptedtypes):
    """Creates a dictionary mapping types to objects of that type.

    Starting with a list of object, and a list of types, this returns a
    dictionary mapping each type to a list of objects of that type.

    For example::

        >>> import types
        >>> filter_discrete_types( ['hello',1,2,'world'], ( basestring, types.IntType) ) #doctest: +NORMALIZE_WHITESPACE
        {<type 'basestring'>: ['hello', 'world'], <type 'int'>: [1, 2]}


    The function checks that each object is mapped to exactly one type
    """

    res = dict([(a, []) for a in acceptedtypes])
    for obj in lst:
        obj_type = filter_expect_single(
            acceptedtypes, lambda at: isinstance(obj, at),
            error_func='{} could not be mapped to a single type'.format(obj))
        res[obj_type].append(obj)
    return res


def assert_no_duplicates(lst, error_func=None):
    """Check for duplicates in a sequence.

    This function checks that a list contains no duplicates, by casting the
    list to a set and comparing the lengths. (This means that we cannot compare
    sequences containing unhashable types, like dictionaries and lists).

    It raises an `NineMLRuntimeError` if the lengths are not equal.
    """
    # Ensure it is a list not a generator
    lst = list(lst)
    if len(lst) != len(set(lst)):
        # Find the duplication:
        seen_hashes = []
        duplicate_hashes = []
        duplicates = []
        for item in lst:
            hsh = hash(item)
            if hsh in seen_hashes:
                if hsh not in duplicate_hashes:
                    duplicate_hashes.append(hsh)
                    duplicates.append(next(i for i in lst
                                           if hash(i) == hsh))
                duplicates.append(item)
            else:
                seen_hashes.append(hsh)
        _dispatch_error_func(
            error_func,
            "Unxpected duplications:\n{}\nFound in list:\n {}"
            .format(repr(duplicates), repr(lst)))


def invert_dictionary(dct):
    """Takes a dictionary mapping (keys => values) and returns a
    new dictionary mapping (values => keys).
    i.e. given a dictionary::

        {k1:v1, k2:v2, k3:v3, ...}

    it returns a dictionary::

        {v1:k1, v2:k2, v3:k3, ...}

    It checks to make sure that no values are duplicated before converting.
    """

    for v in dct.values():
        if not _is_hashable(v):
            err = "Can't invert a dictionary containing unhashable keys"
            raise NineMLRuntimeError(err)

    assert_no_duplicates(dct.values())
    return dict(zip(dct.values(), dct.keys()))


def flatten_first_level(nested_list):
    """Flattens the first level of an iterable, i.e.

        >>> flatten_first_level( [ ['This','is'],['a','short'],['phrase'] ] ) #doctest: +NORMALIZE_WHITESPACE
        ['This', 'is', 'a', 'short', 'phrase']

        >>> flatten_first_level( [ [1,2],[3,4,5],[6] ] ) #doctest: +NORMALIZE_WHITESPACE
        [1,2,3,4,5,6]

    """
    if isinstance(nested_list, basestring):
        err = "Shouldn't pass a string to flatten_first_level."
        err += "Use list(str) instead"
        raise NineMLRuntimeError(err)

    if not _is_iterable(nested_list):
        err = 'flatten_first_level() expects an iterable'
        raise NineMLRuntimeError(err)

    for nl in nested_list:
        if not _is_iterable(nl):
            err = 'flatten_first_level() expects all arguments to be iterable'
            raise NineMLRuntimeError(err)

    return list(itertools.chain(*nested_list))


def safe_dictionary_merge(dictionaries):
    """Safely merge multiple dictionaries into one

    Merges an iterable of dictionaries into a new single dictionary,
    checking that there are no key collisions

    >>> safe_dictionary_merge( [ {1:'One',2:'Two'},{3:'Three'} ] ) #doctest: +NORMALIZE_WHITESPACE
    {1: 'One', 2: 'Two', 3: 'Three'}

    >>> safe_dictionary_merge( [ {1:'One',2:'Two'},{3:'Three',1:'One'} ] ) #doctest: +NORMALIZE_WHITESPACE +IGNORE_EXCEPTION_DETAIL +SKIP
    NineMLRuntimeError: Key Collision while merging dictionarys

    """
    kv_pairs = list(itertools.chain(*[d.iteritems() for d in dictionaries]))
    keys, values = zip(*kv_pairs)
    assert_no_duplicates(keys, 'Key collision while merging dictionarys')
    return dict(kv_pairs)


# TODO: DOCUMENT THESE:
def join_norm(*args):
    return normpath(join(*args))


class LocationMgr(object):
    std_append_to_path_called = False
    import tempfile
    temp_dir = str(tempfile.gettempdir())

    @classmethod
    def getRootDir(cls):
        localDir = realpath(dirname(__file__))
        rootDir = join_norm(localDir, "../../../")
        return rootDir

    @classmethod
    def getPythonPackageRootDir(cls):
        return realpath(dirname(__file__))

    @classmethod
    def getComponentDir(cls):
        # localDir = realpath ( dirname( __file__ ) )
        return join_norm(cls.getPythonPackageRootDir(), '..', 'examples',
                         '_old', 'sample_components')

    @classmethod
    def getTmpDir(cls):
        if not exists(cls.temp_dir):
            raise NineMLRuntimeError("tmp_dir does not exist:%s" % cls.tmp_dir)
        return cls.temp_dir + '/'

    # For developers:
    @classmethod
    def getCatalogDir(cls):
        return join_norm(cls.getRootDir(), "catalog/")


class Settings(object):
    enable_component_validation = True

    enable_nmodl_gsl = True
    use_developer_path = False


def check_list_contain_same_items(lst1, lst2, desc1="", desc2="", ignore=[],
                                  desc=""):
    set1 = set(lst1)
    set2 = set(lst2)
    for i in ignore:
        set1.discard(i)
        set2.discard(i)
    # Are the lists subsets of each other.
    if not set1.issubset(set2) or not set2.issubset(set1):
        errmsg = "Lists were suppose to contain the same elements, but don't!!"
        if desc:
            errmsg += '\n' + desc
        errmsg += "\n1: [%s]: %s" % (desc1, sorted(set1))
        errmsg += "\n2: [%s]: %s" % (desc2, sorted(set2))
        errmsg += "\nElements in : 1 (not 2): %s" % (sorted(set1 - set2))
        errmsg += "\nElements in : 2 (not 1): %s" % (sorted(set2 - set1))
        raise NineMLRuntimeError(errmsg)


def safe_dict(vals):
    """ Create a dict, like dict(), but ensure no duplicate keys are given!
    [Python silently allows dict( [(1:True),(1:None)] ) !!"""
    d = {}
    for k, v in vals:
        if k in vals:
            err = 'safe_dict() failed with duplicated keys: %s' % k
            raise NineMLRuntimeError(err)
        d[k] = v
    if len(vals) != len(d):
        raise NineMLRuntimeError('Duplicate keys given')
    return d


def file_sha1_hexdigest(filename):
    """Returns the SHA1 hex-digest of a file"""

    f = open(filename, 'rb')
    hashhex = hashlib.sha1(f.read()).hexdigest()
    f.close()
    return hashhex


def ensure_iterable(expected_list):
    if isinstance(expected_list, dict):
        raise TypeError("Expected a list, got a dictionary ({})"
                        .format(expected_list))
    elif isinstance(expected_list, (basestring, ContainerObject)):
        lst = [expected_list]
    elif isinstance(expected_list, collections.Iterable):
        lst = list(expected_list)
    else:
        lst = [expected_list]
    return lst


def none_to_empty_list(obj):
    if obj is None:
        return []
    else:
        return obj


def normalise_parameter_as_list(param):
    return ensure_iterable(none_to_empty_list(param))


def restore_sys_path(func):
    """Decorator used to restore the sys.path
    to the value it was before the function call.
    This is useful for loading modules.
    """
    def newfunc(*args, **kwargs):
        oldpath = sys.path[:]
        try:
            return func(*args, **kwargs)
        finally:
            sys.path = oldpath
    return newfunc


class curry:
    """
    http://code.activestate.com/recipes/
    52549-curry-associating-parameters-with-a-function/
    """
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(*(self.pending + args), **kw)

# Matches strings starting with an alphabetic character and ending with an
# alphanumeric character and allowing alphanumeric+underscore characters in
# between.
valid_identifier_re = re.compile(r'[a-zA-Z](\w*[a-zA-Z0-9])?$')


def ensure_valid_identifier(name):
    if valid_identifier_re.match(name) is None:
        raise NineMLRuntimeError(
            "Invalid identifier '{}'. Identifiers must start with an "
            "alphabetic character, only contain alphnumeric and "
            "underscore characters, and end with a alphanumeric character "
            "i.e. not start or end with an underscore".format(name))

valid_uri_re = re.compile(r'^(?:https?|file)://'  # http:// or https://
                          r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
                          r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
                          r'localhost|'  # localhost
                          r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                          r'(?::\d+)?'  # optional port
                          r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def walk(obj, visitor=None, depth=0):
    if visitor:
        visitor.depth = depth
    try:
        obj.accept_visitor(visitor)
    except AttributeError:
        pass
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


def check_units(units, dimension):
    # FIXME: primitive unit checking, should really use Pint, Quantities or
    # Mike Hull's tools
    if not dimension:
        raise ValueError("dimension not specified")
    base_units = {
        "voltage": "V",
        "current": "A",
        "conductance": "S",
        "capacitance": "F",
        "time": "s",
        "frequency": "Hz",
        "dimensionless": "",
    }
    if len(units) == 1:
        base = units
    else:
        base = units[1:]
    if base != base_units[dimension]:
        raise ValueError("Units %s are invalid for dimension %s" %
                         (units, dimension))


def nearly_equal(float1, float2, places=15):
    """
    Determines whether two floating point numbers are nearly equal (to
    within reasonable rounding errors
    """
    mantissa1, exp1 = math.frexp(float1)
    mantissa2, exp2 = math.frexp(float2)
    return (round(mantissa1, places) == round(mantissa2, places) and
            exp1 == exp2)


@restore_sys_path
def load_py_module(filename):
    """Takes the fully qualified path of a python file,
    loads it and returns the module object
    """

    if not os.path.exists(filename):
        print "CWD:", os.getcwd()
        raise NineMLRuntimeError('File does not exist %s' % filename)

    dirname, fname = os.path.split(filename)
    sys.path = [dirname] + sys.path

    module_name = fname.replace('.py', '')

    module = __import__(module_name)
    return module


class TestableComponent(object):

    @classmethod
    def list_available(cls):
        """Returns a list of strings, of the available components"""
        compdir = LocationMgr.getComponentDir()
        comps = []
        for fname in os.listdir(compdir):
            fname, ext = os.path.splitext(fname)
            if not ext == '.py':
                continue
            if fname == '__init__':
                continue
            comps.append(fname)
        return comps

    functor_name = 'get_component'
    metadata_name = 'ComponentMetaData'

    def __str__(self):
        s = ('Testable Component from %s [MetaData=%s]' %
             (self.filename, self.has_metadata))
        return s

    def has_metadata(self):
        return self.metadata is not None

    def __call__(self):
        return self.component_functor()

    def __init__(self, filename):
        cls = TestableComponent

        # If we recieve a filename like 'iaf', that doesn't
        # end in '.py', then lets prepend the component directory
        # and append .py
        if not filename.endswith('.py'):
            compdir = LocationMgr.getComponentDir()
            filename = os.path.join(compdir, '%s.py' % filename)

        self.filename = filename
        self.mod = load_py_module(filename)

        # Get the component functor:
        if cls.functor_name not in self.mod.__dict__.keys():
            err = """Can't load TestableComponnet from %s""" % self.filename
            err += """Can't find required method: %s""" % cls.functor_name
            raise NineMLRuntimeError(err)

        self.component_functor = self.mod.__dict__[cls.functor_name]

        # Check the functor will actually return us an object:
        try:
            c = self.component_functor()
        except Exception, e:
            raise NineMLRuntimeError('component_functor() threw an exception:'
                                     '{}'.format(e))

        if c.__class__.__name__ != 'Dynamics':
            raise NineMLRuntimeError('Functor does not return Component Class')

        # Try and get the meta-data
        self.metadata = None
        if cls.metadata_name in self.mod.__dict__.keys():
            self.metadata = self.mod.__dict__[cls.metadata_name]
