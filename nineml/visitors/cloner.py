from .base import BaseVisitor


class Cloner(BaseVisitor):

    def action(self, obj, nineml_cls, **kwargs):
        pass

    def post_action(self, obj, results, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        kwargs = {}
        for attr in nineml_cls.nineml_attrs:
            kwargs[attr] = getattr(obj, attr)
        for attr in nineml_cls.child_attrs:
            kwargs[attr] = results.attr_result[attr]
        for child_type in nineml_cls.children_types:
            kwargs[child_type._children_iter_name()] = list(
                results.child_results(child_type))
        return nineml_cls(**kwargs)
