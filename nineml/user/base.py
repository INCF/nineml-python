from ..base import BaseNineMLObject
from nineml.exceptions import NineMLRuntimeError, NineMLMissingElementError
from nineml.reference import Reference


class BaseULObject(BaseNineMLObject):

    """
    Base class for user layer classes
    """

    def __init__(self):
        BaseNineMLObject.__init__(self)

#     def set_local_reference(self, document, overwrite=False):
#         """
#         Creates a reference for the object in the provided document either if
#         it is not already from a reference or overwrite is set to true
#         """
#         if self.from_reference is None or overwrite:
#             try:
#                 doc_obj = document[self.name]
#                 if doc_obj != self:
#                     raise NineMLRuntimeError(
#                         "Cannot create reference for '{}' {} in the provided "
#                         "document due to name clash with existing {} "
#                         "object".format(self.name, type(self), type(doc_obj)))
#             except NineMLMissingElementError:
#                 document.add(self)
#             self.from_reference = Reference(self.name, document, url=None)

    def __lt__(self, other):
        if self.__class__.__name__ < other.__class__.__name__:
            return True
        else:
            return self.name < other.name
