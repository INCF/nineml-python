from .base import BaseVisitorWithContext
from ..base import DocumentLevelObject
from nineml.exceptions import NineMLDuplicateObjectError


class NoDuplicatedObjectsValidator(BaseVisitorWithContext):

    def __init__(self, nineml_obj, **kwargs):  # @UnusedVariable
        BaseVisitorWithContext.__init__(self)
        self.all_objects = {}
        self.visit(nineml_obj)

    def default_action(self, nineml_obj, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if not nineml_obj.temporary and not isinstance(nineml_obj,
                                                       DocumentLevelObject):
            if nineml_obj.id in self.all_objects:
                raise NineMLDuplicateObjectError(
                    nineml_obj, tuple(self.contexts),
                    self.all_objects[nineml_obj.id])
            self.all_objects[nineml_obj.id] = tuple(self.contexts)

    def action_dimension(self, dimension, **kwargs):
        pass

    def action_unit(self, unit, **kwargs):
        pass
