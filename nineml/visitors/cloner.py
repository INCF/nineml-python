from .base import BaseChildResultsVisitor
from copy import copy
from nineml.exceptions import NineMLNotBoundException, NineMLUsageError


class Cloner(BaseChildResultsVisitor):
    """
    A Cloner visitor that visits any NineML object (except Documents) and
    creates a copy of the object
    """

    def __init__(self, as_class=None, exclude_annotations=False,
                 clone_definitions=None, document=None,
                 random_seeds=False, validate=True, **kwargs):  # @UnusedVariable @IgnorePep8
        super(Cloner, self).__init__()
        self.as_class = as_class if as_class is not None else type(None)
        self.validate = validate
        self.memo = {}
        self.exclude_annotations = exclude_annotations
        self.document = document
        if clone_definitions is None:
            if document is not None:
                clone_definitions = 'local'
            else:
                clone_definitions = 'all'
        elif clone_definitions == 'local' and document is None:
            raise NineMLUsageError(
                "'document' kwarg must be provided if clone_definitions is "
                " set to 'local'")
        self.clone_definitions = clone_definitions
        self.random_seeds = random_seeds
        self.refs = []

    def clone(self, obj, **kwargs):
        return self.visit(obj, **kwargs)

    def visit(self, obj, nineml_cls=None, **kwargs):
        """
        Before using the inherit visit method, the 'memo' cache is checked
        for previously cloned objects by this cloner. This avoids problems
        with circular references.

        NB: Temporary objects generated when flattening a MultiDynamics object
        (e.g. _NamespaceObject, _MultiRegime, MultiTransition), which can't
        be referenced by their memory position as the memory is freed after
        they go out of scope, are not saved in # the memo.
        """
        if obj.temporary:
            assert nineml_cls is not None or isinstance(obj, self.as_class)
            id_ = None
        else:
            id_ = id(obj)
        try:
            # See if the attribute has already been cloned in memo
            clone = self.memo[id_]
        except KeyError:
            clone = super(Cloner, self).visit(obj, nineml_cls=nineml_cls,
                                              **kwargs)
            # Clone annotations if they are present
            if (hasattr(obj, 'annotations') and not self.exclude_annotations):
                clone._annotations = self.visit(obj.annotations, **kwargs)
            if not obj.temporary:
                self.memo[id_] = clone
        return clone

    def default_action(self, obj, nineml_cls, child_results,
                       children_results, **kwargs):  # @UnusedVariable @IgnorePep8
        init_args = {}
        for attr_name in nineml_cls.nineml_attr:
            try:
                init_args[attr_name] = getattr(obj, attr_name)
            except NineMLNotBoundException:
                init_args[attr_name] = None
        for child_name in nineml_cls.nineml_child:
            try:
                init_args[child_name] = child_results[child_name]
            except KeyError:
                init_args[child_name] = None
        for child_type in nineml_cls.nineml_children:
            init_args[child_type._children_iter_name()] = children_results[
                child_type]
        if hasattr(nineml_cls, 'validate') and not self.validate:
            init_args['validate'] = False
        return nineml_cls(**init_args)

    def action_definition(self, definition, nineml_cls, child_results,
                          children_results, **kwargs):  # @UnusedVariable
        if self.clone_definitions == 'all' or (
            self.clone_definitions == 'local' and
                definition._target.document is self.document):
            target = child_results['target']
        else:
            target = definition.target
        clone = nineml_cls(target=target)
        self.refs.append(clone)
        return clone

    def action__connectivity(self, connectivity, nineml_cls, child_results,
                             children_results, **kwargs):  # @UnusedVariable
        if self.random_seeds:
            random_seed = connectivity._seed
        else:
            random_seed = None
        clone = nineml_cls(
            child_results['rule_properties'],
            random_seed=random_seed,
            source_size=connectivity.source_size,
            destination_size=connectivity.destination_size,
            **kwargs)
        return clone

    def action_reference(self, reference, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Typically won't be called unless Reference is created and referenced
        explicitly as the referenced object themselves is typically referred
        to in the containing container.
        """
        return copy(reference)
