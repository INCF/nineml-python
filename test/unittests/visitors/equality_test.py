import unittest
from nineml.utils.testing.comprehensive import (
    all_types, instances_of_all_types)


for nineml_type in all_types.itervalues():
    defining_attrs = set((a[1:] if a.startswith('_') else a)
                         for a in nineml_type.defining_attributes)
    nineml_attrs = set(
        nineml_type.nineml_attr + tuple(nineml_type.nineml_child.keys()) +
        tuple(c._children_iter_name() for c in nineml_type.nineml_children))
    if defining_attrs != nineml_attrs:
        missing = defining_attrs - nineml_attrs
        extra = nineml_attrs - defining_attrs
        print("{}, missing: {}, extra: {}".format(nineml_type.nineml_type,
                                                  missing, extra))
