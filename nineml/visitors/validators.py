from .base import BaseVisitorWithContext
from nineml.exceptions import NineMLDuplicateObjectError


class NoDuplicatedObjectsValidator(BaseVisitorWithContext):

    def __init__(self, nineml_obj, **kwargs):  # @UnusedVariable
        BaseVisitorWithContext.__init__(self)
        self.all_objects = {}
        self.visit(nineml_obj)

    def default_action(self, nineml_obj, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if not nineml_obj.temporary:
            if nineml_obj.id in self.all_objects:
                raise NineMLDuplicateObjectError(
                    nineml_obj, self.context, self.all_objects[nineml_obj.id])
            self.all_objects[nineml_obj.id] = self.context

    def action_dimension(self, dimension, **kwargs):
        pass

    def action_unit(self, unit, **kwargs):
        pass
