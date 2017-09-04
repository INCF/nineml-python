from .base import BaseVisitor
from nineml.exceptions import NineMLFoundElementException


class ObjectFinder(BaseVisitor):

    def __init__(self, ref_obj, container):
        super(ObjectFinder, self).__init__()
        self.ref_obj = ref_obj
        self._found = None
        try:
            self.visit(container)
        except NineMLFoundElementException as e:
            self._found = e.element

    @property
    def found(self):
        return self._found

    def action(self, obj, nineml_cls, **kwargs):  # @UnusedVariable
        if obj == self.ref_obj:
            raise NineMLFoundElementException()
