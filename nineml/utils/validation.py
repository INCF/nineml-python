from __future__ import absolute_import
from builtins import next
from past.builtins import basestring
import re
from ..exceptions import NineMLUsageError


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
        raise NineMLUsageError(errmsg)


def assert_no_duplicates(lst, errmsg=None):
    """Check for duplicates in a sequence.

    This function checks that a list contains no duplicates, by casting the
    list to a set and comparing the lengths. (This means that we cannot compare
    sequences containing unhashable types, like dictionaries and lists).

    It raises an `NineMLUsageError` if the lengths are not equal.
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
        if errmsg is None:
            errmsg = ("Unxpected duplications:\n{}\nFound in list:\n {}"
                      .format(repr(duplicates), repr(lst)))
        raise NineMLUsageError(errmsg)


# Matches strings starting with an alphabetic character and ending with an
# alphanumeric character and allowing alphanumeric+underscore characters in
# between.
valid_identifier_re = re.compile(r'[a-zA-Z](\w*[a-zA-Z0-9])?$')


def validate_identifier(name):
    if not isinstance(name, basestring):
        raise NineMLUsageError("'{}' identifier is not a string"
                                 .format(name))
    name = name.strip()
    if valid_identifier_re.match(name) is None:
        raise NineMLUsageError(
            "Invalid identifier '{}'. Identifiers must start with an "
            "alphabetic character, only contain alphnumeric and "
            "underscore characters, and end with a alphanumeric character "
            "i.e. not start or end with an underscore".format(name))
    return str(name)

valid_uri_re = re.compile(r'^(?:https?|file)://'  # http:// or https://
                          r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
                          r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
                          r'localhost|'  # localhost
                          r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                          r'(?::\d+)?'  # optional port
                          r'(?:/?|[/?]\S+)$', re.IGNORECASE)
