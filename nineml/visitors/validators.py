from .base import BaseVisitor
from nineml.utils import assert_no_duplicates


class NoDuplicatedObjectsValidator(BaseVisitor):

    def __init__(self, nineml_obj, **kwargs):  # @UnusedVariable
        BaseVisitor.__init__(self)
        self.all_objects = list()
        self.visit(nineml_obj)
        assert_no_duplicates(self.all_objects)

    def default_action(self, nineml_obj, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(nineml_obj)

    def action_dimension(self, dimension, **kwargs):
        pass

    def action_unit(self, unit, **kwargs):
        pass
