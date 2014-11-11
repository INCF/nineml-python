from operator import and_


class BaseALObject(object):

    """
    Base class for abstraction layer classes
    """

    def __eq__(self, other):
        return reduce(and_, [isinstance(other, self.__class__)] +
                            [getattr(self, name) == getattr(other, name)
                             for name in self.__class__.defining_attributes])

    def __ne__(self, other):
        return not self == other
