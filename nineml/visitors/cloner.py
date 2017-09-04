from .base import BaseVisitor
from copy import copy
from nineml.exceptions import NineMLNotBoundException


class Cloner(BaseVisitor):

    def __init__(self, visit_as_class=None, exclude_annotations=False,
                 clone_definitions=True, **kwargs):  # @UnusedVariable
        super(Cloner, self).__init__()
        self.visit_as_class = visit_as_class
        self.memo = {}
        self.exclude_annotations = exclude_annotations
        self.clone_definitions = clone_definitions
        self.refs = []

    def visit(self, obj, nineml_cls=None, **kwargs):
        clone_id = self.clone_id(obj)
        try:
            # See if the attribute has already been cloned in memo
            results = self.Results(None, self.memo[clone_id])
        except KeyError:
            results = super(Cloner, self).visit(obj, nineml_cls=nineml_cls,
                                                **kwargs)
            self.memo[clone_id] = results.post_action
        return results

    def action(self, obj, nineml_cls, **kwargs):
        pass

    def default_post_action(self, obj, results, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        init_args = {}
        for attr in nineml_cls.nineml_attrs:
            try:
                init_args[attr] = getattr(obj, attr)
            except NineMLNotBoundException:
                init_args[attr] = None
        for attr in nineml_cls.child_attrs:
            try:
                init_args[attr] = results.attr_result(attr).post_action
            except KeyError:
                init_args[attr] = None
        for child_type in nineml_cls.children_types:
            init_args[child_type._children_iter_name()] = [
                r.post_action for r in results.child_results(child_type)]
        results.post_action = nineml_cls(**init_args)

    @classmethod
    def clone_id(cls, obj):
        """
        Used in storing cloned objects in 'memo' dictionary to avoid duplicate
        clones of the same object referenced from different points in a complex
        data tree. First looks for special method 'clone_id' and falls back on
        the 'id' function that returns a memory-address based ID.

        Parameters
        ----------
        obj : object
            Any object
        """
        try:
            return obj.clone_id
        except AttributeError:
            return id(obj)

    def post_action_definition(self, definition, results, nineml_cls,
                               **kwargs):
        if self.clone_definitions == 'all' or (
            self.clone_definitions == 'local' and
                definition._target.document is None):
            target = self.visit(
                definition.target, **kwargs).post_action
        else:
            target = definition.target
        clone = nineml_cls(target=target)
        self.refs.append(clone)
        results.post_action = clone

    def post_action_reference(self, reference, results, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Typically won't be called unless Reference is created and referenced
        explicitly as the referenced object themselves is typically referred
        to in the containing container.
        """
        results.post_action = copy(reference)


    def post_action_nineml(self, doc, results, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        To clone NineML Documents
        """
        results.post_action = nineml_cls(*doc.values(), clone=True, **kwargs)
