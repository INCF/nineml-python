from .base import BaseVisitor


class Cloner(BaseVisitor):

    def __init__(self, visit_as_class=None, exclude_annotations=False,
                 clone_definitions=True, **kwargs):  # @UnusedVariable
        super(Cloner, self).__init__()
        self.visit_as_class = visit_as_class
        self.memo = {}
        self.exclude_annotations = exclude_annotations
        self.clone_definitions = clone_definitions

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
        kwargs = {}
        for attr in nineml_cls.nineml_attrs:
            kwargs[attr] = getattr(obj, attr)
        for attr in nineml_cls.child_attrs:
            kwargs[attr] = results.attr_result(attr).post_action
        for child_type in nineml_cls.children_types:
            kwargs[child_type._children_iter_name()] = [
                r.post_action for r in results.child_results(child_type)]
        results.post_action = nineml_cls(**kwargs)

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
