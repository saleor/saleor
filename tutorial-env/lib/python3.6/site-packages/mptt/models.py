from functools import reduce, wraps
import operator
import threading

from django.db import models
from django.db.models.base import ModelBase
from django.db.models.query import Q
from django.db.models.query_utils import DeferredAttribute

from django.utils.translation import ugettext as _

from mptt.compat import cached_field_value
from mptt.fields import TreeForeignKey, TreeOneToOneField, TreeManyToManyField
from mptt.managers import TreeManager
from mptt.signals import node_moved
from mptt.utils import _get_tree_model


__all__ = (
    'TreeForeignKey', 'TreeOneToOneField', 'TreeManyToManyField',
    'TreeManager', 'MPTTOptions', 'MPTTModelBase', 'MPTTModel',
)


class _classproperty:
    def __init__(self, getter, setter=None):
        self.fget = getter
        self.fset = setter

    def __get__(self, cls, owner):
        return self.fget(owner)

    def __set__(self, cls, owner, value):
        if not self.fset:
            raise AttributeError("This classproperty is read only")
        self.fset(owner, value)


class classpropertytype(property):
    def __init__(self, name, bases=(), members={}):
        return super(classpropertytype, self).__init__(
            members.get('__get__'),
            members.get('__set__'),
            members.get('__delete__'),
            members.get('__doc__')
        )


classproperty = classpropertytype('classproperty')


class MPTTOptions:
    """
    Options class for MPTT models. Use this as an inner class called ``MPTTMeta``::

        class MyModel(MPTTModel):
            class MPTTMeta:
                order_insertion_by = ['name']
                parent_attr = 'myparent'
    """

    order_insertion_by = []
    left_attr = 'lft'
    right_attr = 'rght'
    tree_id_attr = 'tree_id'
    level_attr = 'level'
    parent_attr = 'parent'

    def __init__(self, opts=None, **kwargs):
        # Override defaults with options provided
        if opts:
            opts = list(opts.__dict__.items())
        else:
            opts = []
        opts.extend(list(kwargs.items()))

        if 'tree_manager_attr' in [opt[0] for opt in opts]:
            raise ValueError(
                "`tree_manager_attr` has been removed; you should instantiate"
                " a TreeManager as a normal manager on your model instead.")

        for key, value in opts:
            if key[:2] == '__':
                continue
            setattr(self, key, value)

        # Normalize order_insertion_by to a list
        if isinstance(self.order_insertion_by, str):
            self.order_insertion_by = [self.order_insertion_by]
        elif isinstance(self.order_insertion_by, tuple):
            self.order_insertion_by = list(self.order_insertion_by)
        elif self.order_insertion_by is None:
            self.order_insertion_by = []

    def __iter__(self):
        return ((k, v) for k, v in self.__dict__.items() if k[0] != '_')

    # Helper methods for accessing tree attributes on models.
    def get_raw_field_value(self, instance, field_name):
        """
        Gets the value of the given fieldname for the instance.
        This is not the same as getattr().
        This function will return IDs for foreignkeys etc, rather than doing
        a database query.
        """
        field = instance._meta.get_field(field_name)
        return field.value_from_object(instance)

    def set_raw_field_value(self, instance, field_name, value):
        """
        Sets the value of the given fieldname for the instance.
        This is not the same as setattr().
        This function requires an ID for a foreignkey (etc) rather than an instance.
        """
        field = instance._meta.get_field(field_name)
        setattr(instance, field.attname, value)

    def update_mptt_cached_fields(self, instance):
        """
        Caches (in an instance._mptt_cached_fields dict) the original values of:
         - parent pk
         - fields specified in order_insertion_by

        These are used in save() to determine if the relevant fields have changed,
        so that the MPTT fields need to be updated.
        """
        instance._mptt_cached_fields = {}
        field_names = set((self.parent_attr,))
        if self.order_insertion_by:
            for f in self.order_insertion_by:
                if f[0] == '-':
                    f = f[1:]
                field_names.add(f)
        deferred_fields = instance.get_deferred_fields()
        for field_name in field_names:
            if deferred_fields:
                field = instance._meta.get_field(field_name)
                if field.attname in deferred_fields \
                        and field.attname not in instance.__dict__:
                    # deferred attribute (i.e. via .only() or .defer())
                    # It'd be silly to cache this (that'd do a database query)
                    # Instead, we mark it as a deferred attribute here, then
                    # assume it hasn't changed during save(), unless it's no
                    # longer deferred.
                    instance._mptt_cached_fields[field_name] = DeferredAttribute
                    continue
            instance._mptt_cached_fields[field_name] = self.get_raw_field_value(
                instance, field_name)

    def insertion_target_filters(self, instance, order_insertion_by):
        """
        Creates a filter which matches suitable right siblings for ``node``,
        where insertion should maintain ordering according to the list of
        fields in ``order_insertion_by``.

        For example, given an ``order_insertion_by`` of
        ``['field1', 'field2', 'field3']``, the resulting filter should
        correspond to the following SQL::

           field1 > %s
           OR (field1 = %s AND field2 > %s)
           OR (field1 = %s AND field2 = %s AND field3 > %s)

        """
        fields = []
        filters = []
        fields__append = fields.append
        filters__append = filters.append
        and_ = operator.and_
        or_ = operator.or_
        for field_name in order_insertion_by:
            if field_name[0] == '-':
                field_name = field_name[1:]
                filter_suffix = '__lt'
            else:
                filter_suffix = '__gt'
            value = getattr(instance, field_name)
            if value is None:
                # node isn't saved yet. get the insertion value from pre_save.
                field = instance._meta.get_field(field_name)
                value = field.pre_save(instance, True)

            if value is None:
                # we have to use __isnull instead of __lt or __gt becase __lt = Null is invalid
                # depending on order, we need to find the first node where code is null or not null
                value = (filter_suffix == '__lt')
                filter_suffix = '__isnull'

            q = Q(**{field_name + filter_suffix: value})

            filters__append(reduce(and_, [Q(**{f: v}) for f, v in fields] + [q]))
            fields__append((field_name, value))
        return reduce(or_, filters)

    def get_ordered_insertion_target(self, node, parent):
        """
        Attempts to retrieve a suitable right sibling for ``node``
        underneath ``parent`` (which may be ``None`` in the case of root
        nodes) so that ordering by the fields specified by the node's class'
        ``order_insertion_by`` option is maintained.

        Returns ``None`` if no suitable sibling can be found.
        """
        right_sibling = None
        # Optimisation - if the parent doesn't have descendants,
        # the node will always be its last child.
        if parent is None or parent.get_descendant_count() > 0:
            opts = node._mptt_meta
            order_by = opts.order_insertion_by[:]
            filters = self.insertion_target_filters(node, order_by)
            if parent:
                filters = filters & Q(**{opts.parent_attr: parent})
                # Fall back on tree ordering if multiple child nodes have
                # the same values.
                order_by.append(opts.left_attr)
            else:
                filters = filters & Q(**{opts.parent_attr: None})
                # Fall back on tree id ordering if multiple root nodes have
                # the same values.
                order_by.append(opts.tree_id_attr)
            queryset = node.__class__._tree_manager.db_manager(
                node._state.db).filter(filters).order_by(*order_by)
            if node.pk:
                queryset = queryset.exclude(pk=node.pk)
            try:
                right_sibling = queryset[:1][0]
            except IndexError:
                # No suitable right sibling could be found
                pass
        return right_sibling


class MPTTModelBase(ModelBase):
    """
    Metaclass for MPTT models
    """

    def __new__(meta, class_name, bases, class_dict):
        """
        Create subclasses of MPTTModel. This:
         - adds the MPTT fields to the class
         - adds a TreeManager to the model
        """
        if class_name == 'NewBase' and class_dict == {}:
            return super(MPTTModelBase, meta).__new__(meta, class_name, bases, class_dict)
        is_MPTTModel = False
        try:
            MPTTModel
        except NameError:
            is_MPTTModel = True

        MPTTMeta = class_dict.pop('MPTTMeta', None)
        if not MPTTMeta:
            class MPTTMeta:
                pass

        initial_options = frozenset(dir(MPTTMeta))

        # extend MPTTMeta from base classes
        for base in bases:
            if hasattr(base, '_mptt_meta'):
                for name, value in base._mptt_meta:
                    if name == 'tree_manager_attr':
                        continue
                    if name not in initial_options:
                        setattr(MPTTMeta, name, value)

        class_dict['_mptt_meta'] = MPTTOptions(MPTTMeta)
        super_new = super(MPTTModelBase, meta).__new__
        cls = super_new(meta, class_name, bases, class_dict)
        cls = meta.register(cls)

        # see error cases in TreeManager.disable_mptt_updates for the reasoning here.
        cls._mptt_tracking_base = None
        if is_MPTTModel:
            bases = [cls]
        else:
            bases = [base for base in cls.mro() if issubclass(base, MPTTModel)]
        for base in bases:
            if (not (base._meta.abstract or base._meta.proxy) and
                    base._tree_manager.tree_model is base):
                cls._mptt_tracking_base = base
                break
        if cls is cls._mptt_tracking_base:
            cls._threadlocal = threading.local()
            # set on first access (to make threading errors more obvious):
            #    cls._threadlocal.mptt_delayed_tree_changes = None

        return cls

    @classmethod
    def register(meta, cls, **kwargs):
        """
        For the weird cases when you need to add tree-ness to an *existing*
        class. For other cases you should subclass MPTTModel instead of calling this.
        """

        if not issubclass(cls, models.Model):
            raise ValueError(_("register() expects a Django model class argument"))

        if not hasattr(cls, '_mptt_meta'):
            cls._mptt_meta = MPTTOptions(**kwargs)

        abstract = getattr(cls._meta, 'abstract', False)

        try:
            MPTTModel
        except NameError:
            # We're defining the base class right now, so don't do anything
            # We only want to add this stuff to the subclasses.
            # (Otherwise if field names are customized, we'll end up adding two
            # copies)
            pass
        else:
            if not issubclass(cls, MPTTModel):
                bases = list(cls.__bases__)

                # strip out bases that are strict superclasses of MPTTModel.
                # (i.e. Model, object)
                # this helps linearize the type hierarchy if possible
                for i in range(len(bases) - 1, -1, -1):
                    if issubclass(MPTTModel, bases[i]):
                        del bases[i]

                bases.insert(0, MPTTModel)
                cls.__bases__ = tuple(bases)

            is_cls_tree_model = _get_tree_model(cls) is cls

            if is_cls_tree_model:
                # HACK: _meta.get_field() doesn't work before AppCache.ready in Django>=1.8
                # ( see https://code.djangoproject.com/ticket/24231 )
                # So the only way to get existing fields is using local_fields on all superclasses.
                existing_field_names = set()
                for base in cls.mro():
                    if hasattr(base, '_meta'):
                        existing_field_names.update([f.name for f in base._meta.local_fields])

                mptt_meta = cls._mptt_meta
                indexed_attrs = (mptt_meta.tree_id_attr,)
                field_names = (mptt_meta.left_attr, mptt_meta.right_attr, mptt_meta.tree_id_attr, mptt_meta.level_attr)

                for field_name in field_names:
                    if field_name not in existing_field_names:
                        field = models.PositiveIntegerField(db_index=field_name in indexed_attrs, editable=False)
                        field.contribute_to_class(cls, field_name)

                # Add an index_together on tree_id_attr and left_attr, as these are very
                # commonly queried (pretty much all reads).
                index_together = (cls._mptt_meta.tree_id_attr, cls._mptt_meta.left_attr)
                if index_together not in cls._meta.index_together:
                    cls._meta.index_together += (index_together,)

            # Add a tree manager, if there isn't one already
            if not abstract:
                # make sure we have a tree manager somewhere
                tree_manager = None
                # Use the default manager defined on the class if any
                _meta = cls._meta
                if cls._default_manager and isinstance(cls._default_manager, TreeManager):
                    tree_manager = cls._default_manager
                else:
                    for cls_manager in cls._meta.managers:
                        if isinstance(cls_manager, TreeManager):
                            # prefer any locally defined manager (i.e. keep going if not local)
                            if cls_manager.model is cls:
                                tree_manager = cls_manager
                                break

                if is_cls_tree_model:
                    idx_together = (cls._mptt_meta.tree_id_attr, cls._mptt_meta.left_attr)

                    if idx_together not in cls._meta.index_together:
                        cls._meta.index_together += (idx_together,)

                if tree_manager and tree_manager.model is not cls:
                    tree_manager = tree_manager._copy_to_model(cls)
                elif tree_manager is None:
                    tree_manager = TreeManager()
                tree_manager.contribute_to_class(cls, '_tree_manager')

                # avoid using ManagerDescriptor, so instances can refer to self._tree_manager
                setattr(cls, '_tree_manager', tree_manager)
        return cls


def raise_if_unsaved(func):
    @wraps(func)
    def _fn(self, *args, **kwargs):
        if not self.pk:
            raise ValueError(
                'Cannot call %(function)s on unsaved %(class)s instances'
                % {'function': func.__name__, 'class': self.__class__.__name__}
            )
        return func(self, *args, **kwargs)
    return _fn


class MPTTModel(models.Model, metaclass=MPTTModelBase):
    """
    Base class for tree models.
    """

    class Meta:
        abstract = True

    objects = TreeManager()

    def __init__(self, *args, **kwargs):
        super(MPTTModel, self).__init__(*args, **kwargs)
        self._mptt_meta.update_mptt_cached_fields(self)

    def _mpttfield(self, fieldname):
        translated_fieldname = getattr(self._mptt_meta, fieldname + '_attr')
        return getattr(self, translated_fieldname)

    @_classproperty
    def _mptt_updates_enabled(cls):
        if not cls._mptt_tracking_base:
            return True
        return getattr(cls._mptt_tracking_base._threadlocal, 'mptt_updates_enabled', True)

    # ideally this'd be part of the _mptt_updates_enabled classproperty, but it seems
    # that settable classproperties are very, very hard to do! suggestions please :)
    @classmethod
    def _set_mptt_updates_enabled(cls, value):
        assert cls is cls._mptt_tracking_base,\
            "Can't enable or disable mptt updates on a non-tracking class."
        cls._threadlocal.mptt_updates_enabled = value

    @_classproperty
    def _mptt_is_tracking(cls):
        if not cls._mptt_tracking_base:
            return False
        if not hasattr(cls._threadlocal, 'mptt_delayed_tree_changes'):
            # happens the first time this is called from each thread
            cls._threadlocal.mptt_delayed_tree_changes = None
        return cls._threadlocal.mptt_delayed_tree_changes is not None

    @classmethod
    def _mptt_start_tracking(cls):
        assert cls is cls._mptt_tracking_base,\
            "Can't start or stop mptt tracking on a non-tracking class."
        assert not cls._mptt_is_tracking, "mptt tracking is already started."
        cls._threadlocal.mptt_delayed_tree_changes = set()

    @classmethod
    def _mptt_stop_tracking(cls):
        assert cls is cls._mptt_tracking_base,\
            "Can't start or stop mptt tracking on a non-tracking class."
        assert cls._mptt_is_tracking, "mptt tracking isn't started."
        results = cls._threadlocal.mptt_delayed_tree_changes
        cls._threadlocal.mptt_delayed_tree_changes = None
        return results

    @classmethod
    def _mptt_track_tree_modified(cls, tree_id):
        if not cls._mptt_is_tracking:
            return
        cls._threadlocal.mptt_delayed_tree_changes.add(tree_id)

    @classmethod
    def _mptt_track_tree_insertions(cls, tree_id, num_inserted):
        if not cls._mptt_is_tracking:
            return
        changes = cls._threadlocal.mptt_delayed_tree_changes
        if not num_inserted or not changes:
            return

        if num_inserted < 0:
            deleted = range(tree_id + num_inserted, -num_inserted)
            changes.difference_update(deleted)
        new_changes = set(
            (t + num_inserted if t >= tree_id else t) for t in changes)
        cls._threadlocal.mptt_delayed_tree_changes = new_changes

    @raise_if_unsaved
    def get_ancestors(self, ascending=False, include_self=False):
        """
        Creates a ``QuerySet`` containing the ancestors of this model
        instance.

        This defaults to being in descending order (root ancestor first,
        immediate parent last); passing ``True`` for the ``ascending``
        argument will reverse the ordering (immediate parent first, root
        ancestor last).

        If ``include_self`` is ``True``, the ``QuerySet`` will also
        include this model instance.
        """
        if self.is_root_node():
            if not include_self:
                return self._tree_manager.none()
            else:
                # Filter on pk for efficiency.
                qs = self._tree_manager.filter(pk=self.pk)
        else:
            opts = self._mptt_meta

            order_by = opts.left_attr
            if ascending:
                order_by = '-' + order_by

            left = getattr(self, opts.left_attr)
            right = getattr(self, opts.right_attr)

            if not include_self:
                left -= 1
                right += 1

            qs = self._tree_manager._mptt_filter(
                left__lte=left,
                right__gte=right,
                tree_id=self._mpttfield('tree_id'),
            )

            qs = qs.order_by(order_by)

        if hasattr(self, '_mptt_use_cached_ancestors'):
            # Called during or after a `recursetree` tag.
            # There should be cached parents up to level 0.
            # So we can use them to avoid doing a query at all.
            ancestors = []
            p = self
            if not include_self:
                p = getattr(p, opts.parent_attr)

            while p is not None:
                ancestors.append(p)
                p = getattr(p, opts.parent_attr)

            ancestors.reverse()
            qs._result_cache = ancestors

        return qs

    @raise_if_unsaved
    def get_family(self):
        """
        Returns a ``QuerySet`` containing the ancestors, the model itself
        and the descendants, in tree order.
        """
        opts = self._mptt_meta

        left = getattr(self, opts.left_attr)
        right = getattr(self, opts.right_attr)

        ancestors = Q(**{
            "%s__lte" % opts.left_attr: left,
            "%s__gte" % opts.right_attr: right,
            opts.tree_id_attr: self._mpttfield('tree_id'),
        })

        descendants = Q(**{
            "%s__gte" % opts.left_attr: left,
            "%s__lte" % opts.left_attr: right,
            opts.tree_id_attr: self._mpttfield('tree_id'),
        })

        return self._tree_manager.filter(ancestors | descendants)

    @raise_if_unsaved
    def get_children(self):
        """
        Returns a ``QuerySet`` containing the immediate children of this
        model instance, in tree order.

        The benefit of using this method over the reverse relation
        provided by the ORM to the instance's children is that a
        database query can be avoided in the case where the instance is
        a leaf node (it has no children).

        If called from a template where the tree has been walked by the
        ``cache_tree_children`` filter, no database query is required.
        """
        if hasattr(self, '_cached_children'):
            qs = self._tree_manager.filter(pk__in=[n.pk for n in self._cached_children])
            qs._result_cache = self._cached_children
            return qs
        else:
            if self.is_leaf_node():
                return self._tree_manager.none()

            return self._tree_manager._mptt_filter(parent=self)

    @raise_if_unsaved
    def get_descendants(self, include_self=False):
        """
        Creates a ``QuerySet`` containing descendants of this model
        instance, in tree order.

        If ``include_self`` is ``True``, the ``QuerySet`` will also
        include this model instance.
        """
        if self.is_leaf_node():
            if not include_self:
                return self._tree_manager.none()
            else:
                return self._tree_manager.filter(pk=self.pk)

        opts = self._mptt_meta
        left = getattr(self, opts.left_attr)
        right = getattr(self, opts.right_attr)

        if not include_self:
            left += 1
            right -= 1

        return self._tree_manager._mptt_filter(
            tree_id=self._mpttfield('tree_id'),
            left__gte=left,
            left__lte=right
        )

    def get_descendant_count(self):
        """
        Returns the number of descendants this model instance has.
        """
        if self._mpttfield('right') is None:
            # node not saved yet
            return 0
        else:
            return (self._mpttfield('right') - self._mpttfield('left') - 1) // 2

    @raise_if_unsaved
    def get_leafnodes(self, include_self=False):
        """
        Creates a ``QuerySet`` containing leafnodes of this model
        instance, in tree order.

        If ``include_self`` is ``True``, the ``QuerySet`` will also
        include this model instance (if it is a leaf node)
        """
        descendants = self.get_descendants(include_self=include_self)

        return self._tree_manager._mptt_filter(
            descendants,
            left=(models.F(self._mptt_meta.right_attr) - 1)
        )

    @raise_if_unsaved
    def get_next_sibling(self, *filter_args, **filter_kwargs):
        """
        Returns this model instance's next sibling in the tree, or
        ``None`` if it doesn't have a next sibling.
        """
        qs = self._tree_manager.filter(*filter_args, **filter_kwargs)
        if self.is_root_node():
            qs = self._tree_manager._mptt_filter(
                qs,
                parent=None,
                tree_id__gt=self._mpttfield('tree_id'),
            )
        else:
            qs = self._tree_manager._mptt_filter(
                qs,
                parent__pk=getattr(self, self._mptt_meta.parent_attr + '_id'),
                left__gt=self._mpttfield('right'),
            )

        siblings = qs[:1]
        return siblings and siblings[0] or None

    @raise_if_unsaved
    def get_previous_sibling(self, *filter_args, **filter_kwargs):
        """
        Returns this model instance's previous sibling in the tree, or
        ``None`` if it doesn't have a previous sibling.
        """
        opts = self._mptt_meta
        qs = self._tree_manager.filter(*filter_args, **filter_kwargs)
        if self.is_root_node():
            qs = self._tree_manager._mptt_filter(
                qs,
                parent=None,
                tree_id__lt=self._mpttfield('tree_id'),
            )
            qs = qs.order_by('-' + opts.tree_id_attr)
        else:
            qs = self._tree_manager._mptt_filter(
                qs,
                parent__pk=getattr(self, opts.parent_attr + '_id'),
                right__lt=self._mpttfield('left'),
            )
            qs = qs.order_by('-' + opts.right_attr)

        siblings = qs[:1]
        return siblings and siblings[0] or None

    @raise_if_unsaved
    def get_root(self):
        """
        Returns the root node of this model instance's tree.
        """
        if self.is_root_node() and type(self) == self._tree_manager.tree_model:
            return self

        return self._tree_manager._mptt_filter(
            tree_id=self._mpttfield('tree_id'),
            parent=None,
        ).get()

    @raise_if_unsaved
    def get_siblings(self, include_self=False):
        """
        Creates a ``QuerySet`` containing siblings of this model
        instance. Root nodes are considered to be siblings of other root
        nodes.

        If ``include_self`` is ``True``, the ``QuerySet`` will also
        include this model instance.
        """
        if self.is_root_node():
            queryset = self._tree_manager._mptt_filter(parent=None)
        else:
            parent_id = getattr(self, self._mptt_meta.parent_attr + '_id')
            queryset = self._tree_manager._mptt_filter(parent__pk=parent_id)
        if not include_self:
            queryset = queryset.exclude(pk=self.pk)
        return queryset

    def get_level(self):
        """
        Returns the level of this node (distance from root)
        """
        return getattr(self, self._mptt_meta.level_attr)

    def insert_at(self, target, position='first-child', save=False,
                  allow_existing_pk=False, refresh_target=True):
        """
        Convenience method for calling ``TreeManager.insert_node`` with this
        model instance.
        """
        self._tree_manager.insert_node(
            self, target, position, save, allow_existing_pk=allow_existing_pk,
            refresh_target=refresh_target)

    def is_child_node(self):
        """
        Returns ``True`` if this model instance is a child node, ``False``
        otherwise.
        """
        return not self.is_root_node()

    def is_leaf_node(self):
        """
        Returns ``True`` if this model instance is a leaf node (it has no
        children), ``False`` otherwise.
        """
        return not self.get_descendant_count()

    def is_root_node(self):
        """
        Returns ``True`` if this model instance is a root node,
        ``False`` otherwise.
        """
        return getattr(self, self._mptt_meta.parent_attr + '_id') is None

    @raise_if_unsaved
    def is_descendant_of(self, other, include_self=False):
        """
        Returns ``True`` if this model is a descendant of the given node,
        ``False`` otherwise.
        If include_self is True, also returns True if the two nodes are the same node.
        """
        opts = self._mptt_meta

        if include_self and other.pk == self.pk:
            return True

        if getattr(self, opts.tree_id_attr) != getattr(other, opts.tree_id_attr):
            return False
        else:
            left = getattr(self, opts.left_attr)
            right = getattr(self, opts.right_attr)

            return (
                left > getattr(other, opts.left_attr) and
                right < getattr(other, opts.right_attr))

    @raise_if_unsaved
    def is_ancestor_of(self, other, include_self=False):
        """
        Returns ``True`` if this model is an ancestor of the given node,
        ``False`` otherwise.
        If include_self is True, also returns True if the two nodes are the same node.
        """
        if include_self and other.pk == self.pk:
            return True
        return other.is_descendant_of(self)

    def move_to(self, target, position='first-child'):
        """
        Convenience method for calling ``TreeManager.move_node`` with this
        model instance.

        NOTE: This is a low-level method; it does NOT respect ``MPTTMeta.order_insertion_by``.
        In most cases you should just move the node yourself by setting node.parent.
        """
        self._tree_manager.move_node(self, target, position)

    def _is_saved(self, using=None):
        if not self.pk or self._mpttfield('tree_id') is None:
            return False
        opts = self._meta
        if opts.pk.remote_field is None:
            return True
        else:
            if not hasattr(self, '_mptt_saved'):
                manager = self.__class__._base_manager
                manager = manager.using(using)
                self._mptt_saved = manager.filter(pk=self.pk).exists()
            return self._mptt_saved

    def _get_user_field_names(self):
        """ Returns the list of user defined (i.e. non-mptt internal) field names. """
        from django.db.models.fields import AutoField

        field_names = []
        internal_fields = (
            self._mptt_meta.left_attr, self._mptt_meta.right_attr, self._mptt_meta.tree_id_attr,
            self._mptt_meta.level_attr)
        for field in self._meta.fields:
            if (field.name not in internal_fields) and (not isinstance(field, AutoField)) and (not field.primary_key):  # noqa
                field_names.append(field.name)
        return field_names

    def save(self, *args, **kwargs):
        """
        If this is a new node, sets tree fields up before it is inserted
        into the database, making room in the tree structure as neccessary,
        defaulting to making the new node the last child of its parent.

        It the node's left and right edge indicators already been set, we
        take this as indication that the node has already been set up for
        insertion, so its tree fields are left untouched.

        If this is an existing node and its parent has been changed,
        performs reparenting in the tree structure, defaulting to making the
        node the last child of its new parent.

        In either case, if the node's class has its ``order_insertion_by``
        tree option set, the node will be inserted or moved to the
        appropriate position to maintain ordering by the specified field.
        """
        do_updates = self.__class__._mptt_updates_enabled
        track_updates = self.__class__._mptt_is_tracking

        opts = self._mptt_meta

        if not (do_updates or track_updates):
            # inside manager.disable_mptt_updates(), don't do any updates.
            # unless we're also inside TreeManager.delay_mptt_updates()
            if self._mpttfield('left') is None:
                # we need to set *some* values, though don't care too much what.
                parent = cached_field_value(self, opts.parent_attr)
                # if we have a cached parent, have a stab at getting
                # possibly-correct values.  otherwise, meh.
                if parent:
                    left = parent._mpttfield('left') + 1
                    setattr(self, opts.left_attr, left)
                    setattr(self, opts.right_attr, left + 1)
                    setattr(self, opts.level_attr, parent._mpttfield('level') + 1)
                    setattr(self, opts.tree_id_attr, parent._mpttfield('tree_id'))
                    self._tree_manager._post_insert_update_cached_parent_right(parent, 2)
                else:
                    setattr(self, opts.left_attr, 1)
                    setattr(self, opts.right_attr, 2)
                    setattr(self, opts.level_attr, 0)
                    setattr(self, opts.tree_id_attr, 0)
            return super(MPTTModel, self).save(*args, **kwargs)

        parent_id = opts.get_raw_field_value(self, opts.parent_attr)

        # determine whether this instance is already in the db
        force_update = kwargs.get('force_update', False)
        force_insert = kwargs.get('force_insert', False)
        collapse_old_tree = None
        deferred_fields = self.get_deferred_fields()
        if force_update or (not force_insert and self._is_saved(using=kwargs.get('using'))):
            # it already exists, so do a move
            old_parent_id = self._mptt_cached_fields[opts.parent_attr]
            if old_parent_id is DeferredAttribute:
                same_order = True
            else:
                same_order = old_parent_id == parent_id

            if same_order and len(self._mptt_cached_fields) > 1:
                for field_name, old_value in self._mptt_cached_fields.items():
                    if old_value is DeferredAttribute and field_name not in deferred_fields:
                        same_order = False
                        break
                    if old_value != opts.get_raw_field_value(self, field_name):
                        same_order = False
                        break
                if not do_updates and not same_order:
                    same_order = True
                    self.__class__._mptt_track_tree_modified(self._mpttfield('tree_id'))
            elif (not do_updates) and not same_order and old_parent_id is None:
                # the old tree no longer exists, so we need to collapse it.
                collapse_old_tree = self._mpttfield('tree_id')
                parent = getattr(self, opts.parent_attr)
                tree_id = parent._mpttfield('tree_id')
                left = parent._mpttfield('left') + 1
                self.__class__._mptt_track_tree_modified(tree_id)
                setattr(self, opts.tree_id_attr, tree_id)
                setattr(self, opts.left_attr, left)
                setattr(self, opts.right_attr, left + 1)
                setattr(self, opts.level_attr, parent._mpttfield('level') + 1)
                same_order = True

            if not same_order:
                opts.set_raw_field_value(self, opts.parent_attr, old_parent_id)
                try:
                    right_sibling = None
                    if opts.order_insertion_by:
                        right_sibling = opts.get_ordered_insertion_target(
                            self, getattr(self, opts.parent_attr))

                    if parent_id is not None:
                        parent = getattr(self, opts.parent_attr)
                        # If we aren't already a descendant of the new parent,
                        # we need to update the parent.rght so things like
                        # get_children and get_descendant_count work correctly.
                        #
                        # parent might be None if parent_id was assigned
                        # directly -- then we certainly do not have to update
                        # the cached parent.
                        update_cached_parent = parent and (
                            getattr(self, opts.tree_id_attr) != getattr(parent, opts.tree_id_attr) or  # noqa
                            getattr(self, opts.left_attr) < getattr(parent, opts.left_attr) or
                            getattr(self, opts.right_attr) > getattr(parent, opts.right_attr))

                    if right_sibling:
                        self._tree_manager._move_node(
                            self, right_sibling, 'left', save=False,
                            refresh_target=False)
                    else:
                        # Default movement
                        if parent_id is None:
                            root_nodes = self._tree_manager.root_nodes()
                            try:
                                rightmost_sibling = root_nodes.exclude(
                                    pk=self.pk).order_by('-' + opts.tree_id_attr)[0]
                                self._tree_manager._move_node(
                                    self, rightmost_sibling, 'right', save=False,
                                    refresh_target=False)
                            except IndexError:
                                pass
                        else:
                            self._tree_manager._move_node(
                                self, parent, 'last-child', save=False)

                    if parent_id is not None and update_cached_parent:
                        # Update rght of cached parent
                        right_shift = 2 * (self.get_descendant_count() + 1)
                        self._tree_manager._post_insert_update_cached_parent_right(
                            parent, right_shift)
                finally:
                    # Make sure the new parent is always
                    # restored on the way out in case of errors.
                    opts.set_raw_field_value(self, opts.parent_attr, parent_id)

                # If there were no exceptions raised then send a moved signal
                node_moved.send(sender=self.__class__, instance=self,
                                target=getattr(self, opts.parent_attr))
            else:
                opts.set_raw_field_value(self, opts.parent_attr, parent_id)
                if not track_updates:
                    # When not using delayed/disabled updates,
                    # populate update_fields with user defined model fields.
                    # This helps preserve tree integrity when saving model on top
                    # of a modified tree.
                    if len(args) > 3:
                        if not args[3]:
                            args = list(args)
                            args[3] = self._get_user_field_names()
                            args = tuple(args)
                    else:
                        if not kwargs.get("update_fields", None):
                            kwargs["update_fields"] = self._get_user_field_names()

        else:
            # new node, do an insert
            if (getattr(self, opts.left_attr) and getattr(self, opts.right_attr)):
                # This node has already been set up for insertion.
                pass
            else:
                parent = getattr(self, opts.parent_attr)

                right_sibling = None
                # if we're inside delay_mptt_updates, don't do queries to find
                # sibling position.  instead, do default insertion. correct
                # positions will be found during partial rebuild later.
                # *unless* this is a root node. (as update tracking doesn't
                # handle re-ordering of trees.)
                if do_updates or parent is None:
                    if opts.order_insertion_by:
                        right_sibling = opts.get_ordered_insertion_target(self, parent)

                if right_sibling:
                    self.insert_at(right_sibling, 'left', allow_existing_pk=True,
                                   refresh_target=False)

                    if parent:
                        # since we didn't insert into parent, we have to update parent.rght
                        # here instead of in TreeManager.insert_node()
                        right_shift = 2 * (self.get_descendant_count() + 1)
                        self._tree_manager._post_insert_update_cached_parent_right(
                            parent, right_shift)
                else:
                    # Default insertion
                    self.insert_at(parent, position='last-child', allow_existing_pk=True)
        try:
            super(MPTTModel, self).save(*args, **kwargs)
        finally:
            if collapse_old_tree is not None:
                self._tree_manager._create_tree_space(collapse_old_tree, -1)

        self._mptt_saved = True
        opts.update_mptt_cached_fields(self)
    save.alters_data = True

    def delete(self, *args, **kwargs):
        """Calling ``delete`` on a node will delete it as well as its full
        subtree, as opposed to reattaching all the subnodes to its parent node.

        There are no argument specific to a MPTT model, all the arguments will
        be passed directly to the django's ``Model.delete``.

        ``delete`` will not return anything. """
        try:
            # We have to make sure we use database's mptt values, since they
            # could have changed between the moment the instance was retrieved and
            # the moment it is deleted.
            # This happens for example if you delete several nodes at once from a queryset.
            fields_to_refresh = [self._mptt_meta.right_attr,
                                 self._mptt_meta.left_attr,
                                 self._mptt_meta.tree_id_attr,]
            self.refresh_from_db(fields=fields_to_refresh)
        except self.__class__.DoesNotExist as e:
            # In case the object was already deleted, we don't want to throw an exception
            pass
        tree_width = (self._mpttfield('right') -
                      self._mpttfield('left') + 1)
        target_right = self._mpttfield('right')
        tree_id = self._mpttfield('tree_id')
        self._tree_manager._close_gap(tree_width, target_right, tree_id)
        parent = cached_field_value(self, self._mptt_meta.parent_attr)
        if parent:
            right_shift = -self.get_descendant_count() - 2
            self._tree_manager._post_insert_update_cached_parent_right(parent, right_shift)

        return super(MPTTModel, self).delete(*args, **kwargs)
    delete.alters_data = True

    def _mptt_refresh(self):
        if not self.pk:
            return
        manager = type(self)._tree_manager
        opts = self._mptt_meta
        values = manager.using(self._state.db).filter(pk=self.pk).values(
            opts.left_attr,
            opts.right_attr,
            opts.level_attr,
            opts.tree_id_attr,
        )[0]
        for k, v in values.items():
            setattr(self, k, v)
