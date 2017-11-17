from ..base import AnnotatedNineMLObject
# from nineml.exceptions import NineMLUsageError, NineMLNameError
# from nineml.reference import Reference


class BaseULObject(AnnotatedNineMLObject):

    """
    Base class for user layer classes
    """

    layer = 'user'

    def __init__(self, **kwargs):
        AnnotatedNineMLObject.__init__(self, **kwargs)
