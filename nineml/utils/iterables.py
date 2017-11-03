from __future__ import absolute_import
from builtins import zip
from past.builtins import basestring
import itertools
from functools import reduce
import collections
from operator import attrgetter
from .validation import assert_no_duplicates
from ..exceptions import NineMLUsageError
from nineml.base import ContainerObject
from logging import getLogger


logger = getLogger('NineML')


class OrderedDefaultListDict(collections.OrderedDict):

    def __missing__(self, key):
        self[key] = value = []
        return value


def expect_single(lst, errmsg=None):
    """Retrieve a single element from an iterable.

    This function tests whether an iterable contains just a single element and
    if so returns that element. Otherwise it raises an Exception.

    :param lst: An iterable

    :rtype: the element in the list, ``lst[0]``, provided ``len(lst)==1``

    >>> expect_single( ['hello'] )
    'hello'

    >>> expect_single( [1] )
    1

    >>> expect_single( [] ) #doctest: +SKIP
    NineMLUsageError: expect_single() recieved an iterable of length: 0

    >>> expect_single( [None,None] ) #doctest: +SKIP
    NineMLUsageError: expect_single() recieved an iterable of length: 2

    >>> expect_single( [], lambda: raise_exception( RuntimeError('Aggh') ) #doctest: +SKIP  # @IgnorePep8
    RuntimeError: Aggh

    >>> #Slightly more tersly:
    >>> expect_single( [], RuntimeError('Aggh') ) #doctest: +SKIP
    RuntimeError: Aggh

    """
    if isinstance(lst, basestring):
        raise NineMLUsageError(
            "A string rather than a list/tuple was provided to expect_single "
            "({})".format(lst))
    if not _is_iterable(lst):
        raise NineMLUsageError('Object not iterable')
    if issubclass(lst.__class__, (dict)):
        err = "Dictionary passed to expect_single. This could be ambiguous"
        err += "\nIf this is what you intended, please explicity pass '.keys' "
        raise NineMLUsageError(err)

    lst = list(lst)

    # Good case:
    if len(lst) == 1:
        return lst[0]

    if errmsg is None:
        # Bad case: our list doesn't contain just one element
        errmsg = 'expect_single() recieved an iterable of length: %d'.format(
            len(lst))
        errmsg += '\n  - List Contents:{}\n'.format(lst)
    raise NineMLUsageError(errmsg)


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


def filter_expect_single(lst, func=None, errmsg=None):
    """Find a single element matching a predicate in a list.

       This is a syntactic-sugar function ``_filter`` and ``expect_single``
       in a single call.

        Returns::

            expect_single( _filter(lst, func))


        This is useful when we want to find an item in a sequence with a
        certain property, and expect there to be only one.

        Examples:

        >>> find_smith = lambda s: s.split()[-1] == 'Smith'
        >>> filter_expect_single( ['John Smith','Tim Jones'], func=find_smith )  #doctest: +NORMALIZE_WHITESPACE
        'John Smith'

    """
    return expect_single(_filter(lst, func), errmsg)


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
            errmsg='{} could not be mapped to a single type'.format(obj))
        res[obj_type].append(obj)
    return res


def invert_dictionary(dct):
    """Takes a dictionary mapping (keys => values) and returns a
    new dictionary mapping (values => keys).
    i.e. given a dictionary::

        {k1:v1, k2:v2, k3:v3, ...}

    it returns a dictionary::

        {v1:k1, v2:k2, v3:k3, ...}

    It checks to make sure that no values are duplicated before converting.
    """

    for v in list(dct.values()):
        if not _is_hashable(v):
            err = "Can't invert a dictionary containing unhashable keys"
            raise NineMLUsageError(err)

    assert_no_duplicates(list(dct.values()))
    return dict(list(zip(list(dct.values()), list(dct.keys()))))


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
        raise NineMLUsageError(err)

    if not _is_iterable(nested_list):
        err = 'flatten_first_level() expects an iterable'
        raise NineMLUsageError(err)

    for nl in nested_list:
        if not _is_iterable(nl) or isinstance(nl, basestring):
            raise NineMLUsageError(
                "flatten_first_level() expects all arguments to be iterable "
                "and not strings ({})".format(nested_list))
    return list(itertools.chain(*nested_list))


def safe_dictionary_merge(dictionaries):
    """Safely merge multiple dictionaries into one

    Merges an iterable of dictionaries into a new single dictionary,
    checking that there are no key collisions

    >>> safe_dictionary_merge( [ {1:'One',2:'Two'},{3:'Three'} ] ) #doctest: +NORMALIZE_WHITESPACE
    {1: 'One', 2: 'Two', 3: 'Three'}

    >>> safe_dictionary_merge( [ {1:'One',2:'Two'},{3:'Three',1:'One'} ] ) #doctest: +NORMALIZE_WHITESPACE +IGNORE_EXCEPTION_DETAIL +SKIP
    NineMLUsageError: Key Collision while merging dictionarys

    """
    kv_pairs = list(itertools.chain(*[iter(d.items()) for d in dictionaries]))
    keys, _ = list(zip(*kv_pairs))
    assert_no_duplicates(keys, 'Key collision while merging dictionarys')
    return dict(kv_pairs)


def _is_iterable(obj):
    return hasattr(obj, '__iter__')


def _is_hashable(obj):
    try:
        hash(obj)
        return True
    except:
        return False


def unique_by_id(lst):
    """
    Gets a list of unique 9ML objects using their 'id' property. Similar to a
    set but can handle temporary objects as well.

    Typically used in unittests.
    """
    id_map = {}
    for obj in lst:
        id_map[obj.id] = obj
    return sorted(id_map.values(), key=attrgetter('sort_key'))


def unique_by_eq(lst):
    return reduce(lambda l, x: l.append(x) or l if x not in l else l, lst, [])


def ensure_iterable(expected_list):
    if isinstance(expected_list, dict):
        raise TypeError("Expected a list, got a dictionary ({})"
                        .format(expected_list))
    elif isinstance(expected_list, (basestring, ContainerObject)):
        lst = [expected_list]
    elif isinstance(expected_list, collections.Iterable):  # @UndefinedVariable
        lst = list(expected_list)
    else:
        lst = [expected_list]
    return lst


def normalise_parameter_as_list(param):
    return ensure_iterable(none_to_empty_list(param))


def none_to_empty_list(obj):
    if obj is None:
        return []
    else:
        return obj


def safe_dict(vals):
    """ Create a dict, like dict(), but ensure no duplicate keys are given!
    [Python silently allows dict( [(1:True),(1:None)] ) !!"""
    d = {}
    for k, v in vals:
        if k in vals:
            err = 'safe_dict() failed with duplicated keys: %s' % k
            raise NineMLUsageError(err)
        d[k] = v
    if len(vals) != len(d):
        raise NineMLUsageError('Duplicate keys given')
    return d
