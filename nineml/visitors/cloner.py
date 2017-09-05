from .base import BaseVisitor
from copy import copy
from nineml.exceptions import (
    NineMLNotBoundException, NineMLInvalidElementTypeException,
    NineMLRuntimeError)


class Cloner(BaseVisitor):
    """
    A Cloner visitor that visits any NineML object (except Documents) and
    creates a copy of the object
    """

    def __init__(self, visit_as_class=None, exclude_annotations=False,
                 clone_definitions=None, document=None, **kwargs):  # @UnusedVariable @IgnorePep8
        super(Cloner, self).__init__()
        self.visit_as_class = visit_as_class
        self.memo = {}
        self.exclude_annotations = exclude_annotations
        self.document = document
        if clone_definitions is None:
            if document is not None:
                clone_definitions = 'local'
            else:
                clone_definitions = 'all'
        elif clone_definitions == 'local' and document is None:
            raise NineMLRuntimeError(
                "'document' kwarg must be provided if clone_definitions is "
                " set to 'local'")
        self.clone_definitions = clone_definitions
        self.refs = []

    def clone(self, obj, **kwargs):
        results = self.visit(obj, **kwargs)
        return results.post_action

    def visit(self, obj, nineml_cls=None, **kwargs):
        # Temporary objects generated when flattening a MultiDynamics object
        # (e.g. _NamespaceObject, _MultiRegime, MultiTransition), which can't
        # be referenced by their memory position as the memory is freed after
        # they go out of scope, are not saved in # the memo.
        if type(obj).__name__.startswith('_'):
            assert nineml_cls is not None
            id_ = None
        else:
            id_ = id(obj)
        try:
            # See if the attribute has already been cloned in memo
            results = self.Results(None, self.memo[id_])
        except KeyError:
            results = super(Cloner, self).visit(obj, nineml_cls=nineml_cls,
                                                **kwargs)
            clone = results.post_action
            self.copy_index(obj, clone)
            if id_ is not None:
                self.memo[id_] = clone
        return results

    def action(self, obj, nineml_cls, **kwargs):
        pass

    def default_post_action(self, obj, results, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        init_args = {}
        for attr in nineml_cls.nineml_attr:
            try:
                init_args[attr] = getattr(obj, attr)
            except NineMLNotBoundException:
                init_args[attr] = None
        for attr in nineml_cls.nineml_child:
            try:
                init_args[attr] = results.attr_result(attr).post_action
            except KeyError:
                init_args[attr] = None
        for child_type in nineml_cls.nineml_children:
            init_args[child_type._children_iter_name()] = [
                r.post_action for r in results.child_results(child_type)]
        results.post_action = nineml_cls(**init_args)

    def post_action_definition(self, definition, results, nineml_cls,
                               **kwargs):  # @UnusedVariable
        if self.clone_definitions == 'all' or (
            self.clone_definitions == 'local' and
                definition._target.document is self.document):
            target = results.attr_result('target').post_action
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

    def copy_index(self, obj, clone):
        """
        Attempt to copy index if present in parent container
        """
        try:
            index = self.context.parent.index_of(obj)
            self.context.parent_result.post_action._indices[
                obj._child_accessor_name()][clone] = index
        except (AttributeError, NineMLInvalidElementTypeException):
            pass
