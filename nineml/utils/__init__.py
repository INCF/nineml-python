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
from ..exceptions import internal_error
from ..exceptions import NineMLRuntimeError
from nineml.base import ContainerObject
from logging import getLogger


logger = getLogger('lib9ml')


class OrderedDefaultListDict(collections.OrderedDict):

    def __missing__(self, key):
        self[key] = value = []
        return value


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


class Settings(object):
    enable_component_validation = True

    enable_nmodl_gsl = True
    use_developer_path = False


def check_inferred_against_declared(declared, inferred, desc='',
                                    strict_unused=True):
    decl_set = set(declared)
    inf_set = set(inferred)
    if strict_unused:
        fail = decl_set != inf_set
    else:
        fail = bool(inf_set - decl_set)
    # Are the lists subsets of each other.
    if fail:
        errmsg = "Error! Declared items did not match inferred:\n"
        if desc:
            errmsg += '\n' + desc
        errmsg += "\n1: Declared: {}".format(sorted(decl_set))
        errmsg += "\n2: Inferred: {}".format(sorted(inf_set))
        errmsg += ("\nInferred elements not declared: {}"
                   .format(sorted(inf_set - decl_set)))
        if strict_unused:
            errmsg += ("\nDeclared elements not inferred: {}"
                       .format(sorted(decl_set - inf_set)))
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


# Matches strings starting with an alphabetic character and ending with an
# alphanumeric character and allowing alphanumeric+underscore characters in
# between.
valid_identifier_re = re.compile(r'[a-zA-Z](\w*[a-zA-Z0-9])?$')


def ensure_valid_identifier(name):
    if not isinstance(name, basestring):
        raise NineMLRuntimeError("'{}' identifier is not a string"
                                 .format(name))
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


class ExampleVisitor(object):

    def visit(self, obj):
        print " " * self.depth + str(obj)


class Collector(object):

    def __init__(self):
        self.objects = []

    def visit(self, obj):
        self.objects.append(obj)


def nearly_equal(float1, float2, places=15):
    """
    Determines whether two floating point numbers are nearly equal (to
    within reasonable rounding errors
    """
    mantissa1, exp1 = math.frexp(float1)
    mantissa2, exp2 = math.frexp(float2)
    return (round(mantissa1, places) == round(mantissa2, places) and
            exp1 == exp2)

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'\{(.*)\}(.*)')


def strip_xmlns(tag_name):
    return xmlns_re.match(tag_name).group(2)


def xml_equal(xml1, xml2, indent='', annotations=False):
    if xml1.tag != xml2.tag:
        logger.error("{}Tag '{}' doesn't equal '{}'"
                     .format(indent, xml1.tag, xml2.tag))
        return False
    if xml1.attrib != xml2.attrib:
        logger.error("{}Attributes '{}' doesn't equal '{}'"
                     .format(indent, xml1.attrib, xml2.attrib))
        return False
    text1 = xml1.text if xml1.text is not None else ''
    text2 = xml2.text if xml2.text is not None else ''
    if text1.strip() != text2.strip():
        logger.error("{}Body '{}' doesn't equal '{}'"
                     .format(indent, text1, text2))
        return False
    tail1 = xml1.tail if xml1.tail is not None else ''
    tail2 = xml2.tail if xml2.tail is not None else ''
    if tail1.strip() != tail2.strip():
        if text1.strip() != text2.strip():
            logger.error("{}Body '{}' doesn't equal '{}'"
                         .format(indent, tail1, tail2))
        return False
    children1 = [c for c in xml1.getchildren()
                 if not c.tag.endswith('Annotations') or annotations]
    children2 = [c for c in xml2.getchildren()
                 if not c.tag.endswith('Annotations') or annotations]
    if len(children1) != len(children2):
        logger.error("{}Number of children {} doesn't equal {}:\n{}\n{}"
                     .format(indent, len(children1), len(children2),
                             ', '.join(
                                 '{}:{}'.format(strip_xmlns(c.tag),
                                                c.attrib.get('name', None))
                                 for c in children1),
                             ', '.join(
                                 '{}:{}'.format(strip_xmlns(c.tag),
                                                c.attrib.get('name', None))
                                 for c in children2)))
        return False
    return all(xml_equal(c1, c2, indent=indent + '    ')
               for c1, c2 in itertools.izip(children1, children2))
