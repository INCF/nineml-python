from __future__ import absolute_import
import collections


class OrderedDefaultListDict(collections.OrderedDict):

    def __missing__(self, key):
        self[key] = value = []
        return value
