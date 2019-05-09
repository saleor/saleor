"""
Utilities for working with lists of model instances which represent
trees.
"""
import copy
import csv
import itertools
import sys

from django.utils.translation import ugettext as _

__all__ = ('previous_current_next', 'tree_item_iterator',
           'drilldown_tree_for_node', 'get_cached_trees',)


def previous_current_next(items):
    """
    From http://www.wordaligned.org/articles/zippy-triples-served-with-python

    Creates an iterator which returns (previous, current, next) triples,
    with ``None`` filling in when there is no previous or next
    available.
    """
    extend = itertools.chain([None], items, [None])
    prev, cur, nex = itertools.tee(extend, 3)
    # Advancing an iterator twice when we know there are two items (the
    # two Nones at the start and at the end) will never fail except if
    # `items` is some funny StopIteration-raising generator. There's no point
    # in swallowing this exception.
    next(cur)
    next(nex)
    next(nex)
    return zip(prev, cur, nex)


def tree_item_iterator(items, ancestors=False, callback=str):
    """
    Given a list of tree items, iterates over the list, generating
    two-tuples of the current tree item and a ``dict`` containing
    information about the tree structure around the item, with the
    following keys:

       ``'new_level'``
          ``True`` if the current item is the start of a new level in
          the tree, ``False`` otherwise.

       ``'closed_levels'``
          A list of levels which end after the current item. This will
          be an empty list if the next item is at the same level as the
          current item.

    If ``ancestors`` is ``True``, the following key will also be
    available:

       ``'ancestors'``
          A list of representations of the ancestors of the current
          node, in descending order (root node first, immediate parent
          last).

          For example: given the sample tree below, the contents of the
          list which would be available under the ``'ancestors'`` key
          are given on the right::

             Books                    ->  []
                Sci-fi                ->  [u'Books']
                   Dystopian Futures  ->  [u'Books', u'Sci-fi']

          You can overload the default representation by providing an
          optional ``callback`` function which takes a single argument
          and performs coersion as required.

    """
    structure = {}
    opts = None
    first_item_level = 0
    for previous, current, next_ in previous_current_next(items):
        if opts is None:
            opts = current._mptt_meta

        current_level = getattr(current, opts.level_attr)
        if previous:
            structure['new_level'] = (getattr(previous,
                                              opts.level_attr) < current_level)
            if ancestors:
                # If the previous node was the end of any number of
                # levels, remove the appropriate number of ancestors
                # from the list.
                if structure['closed_levels']:
                    structure['ancestors'] = \
                        structure['ancestors'][:-len(structure['closed_levels'])]
                # If the current node is the start of a new level, add its
                # parent to the ancestors list.
                if structure['new_level']:
                    structure['ancestors'].append(callback(previous))
        else:
            structure['new_level'] = True
            if ancestors:
                # Set up the ancestors list on the first item
                structure['ancestors'] = []

            first_item_level = current_level
        if next_:
            structure['closed_levels'] = list(range(
                current_level,
                getattr(next_, opts.level_attr),
                -1))
        else:
            # All remaining levels need to be closed
            structure['closed_levels'] = list(range(
                current_level,
                first_item_level - 1,
                -1))

        # Return a deep copy of the structure dict so this function can
        # be used in situations where the iterator is consumed
        # immediately.
        yield current, copy.deepcopy(structure)


def drilldown_tree_for_node(node, rel_cls=None, rel_field=None, count_attr=None,
                            cumulative=False):
    """
    Creates a drilldown tree for the given node. A drilldown tree
    consists of a node's ancestors, itself and its immediate children,
    all in tree order.

    Optional arguments may be given to specify a ``Model`` class which
    is related to the node's class, for the purpose of adding related
    item counts to the node's children:

    ``rel_cls``
       A ``Model`` class which has a relation to the node's class.

    ``rel_field``
       The name of the field in ``rel_cls`` which holds the relation
       to the node's class.

    ``count_attr``
       The name of an attribute which should be added to each child in
       the drilldown tree, containing a count of how many instances
       of ``rel_cls`` are related through ``rel_field``.

    ``cumulative``
       If ``True``, the count will be for each child and all of its
       descendants, otherwise it will be for each child itself.
    """
    if rel_cls and rel_field and count_attr:
        children = node._tree_manager.add_related_count(
            node.get_children(), rel_cls, rel_field, count_attr, cumulative)
    else:
        children = node.get_children()
    return itertools.chain(node.get_ancestors(), [node], children)


def print_debug_info(qs, file=None):
    """
    Given an mptt queryset, prints some debug information to stdout.
    Use this when things go wrong.
    Please include the output from this method when filing bug issues.
    """
    opts = qs.model._mptt_meta
    writer = csv.writer(sys.stdout if file is None else file)
    header = (
        'pk',
        opts.level_attr,
        '%s_id' % opts.parent_attr,
        opts.tree_id_attr,
        opts.left_attr,
        opts.right_attr,
        'pretty',
    )
    writer.writerow(header)
    for n in qs.order_by('tree_id', 'lft'):
        level = getattr(n, opts.level_attr)
        row = []
        for field in header[:-1]:
            row.append(getattr(n, field))

        row_text = '%s%s' % ('- ' * level, str(n))
        row.append(row_text)
        writer.writerow(row)


def _get_tree_model(model_class):
    # Find the model that contains the tree fields.
    # This is a weird way of going about it, but Django doesn't let us access
    # the fields list to detect where the tree fields actually are,
    # because the app cache hasn't been loaded yet.
    # So, it *should* be the *last* concrete MPTTModel subclass in the mro().
    bases = list(model_class.mro())
    while bases:
        b = bases.pop()
        # NOTE can't use `issubclass(b, MPTTModel)` here because we can't import MPTTModel yet!
        # So hasattr(b, '_mptt_meta') will have to do.
        if hasattr(b, '_mptt_meta') and not (b._meta.abstract or b._meta.proxy):
            return b
    return None


def get_cached_trees(queryset):
    """
    Takes a list/queryset of model objects in MPTT left (depth-first) order and
    caches the children and parent on each node. This allows up and down
    traversal through the tree without the need for further queries. Use cases
    include using a recursively included template or arbitrarily traversing
    trees.

    NOTE: nodes _must_ be passed in the correct (depth-first) order. If they aren't,
    a ValueError will be raised.

    Returns a list of top-level nodes. If a single tree was provided in its
    entirety, the list will of course consist of just the tree's root node.

    For filtered querysets, if no ancestors for a node are included in the
    queryset, it will appear in the returned list as a top-level node.

    Aliases to this function are also available:

    ``mptt.templatetags.mptt_tag.cache_tree_children``
       Use for recursive rendering in templates.

    ``mptt.querysets.TreeQuerySet.get_cached_trees``
       Useful for chaining with queries; e.g.,
       `Node.objects.filter(**kwargs).get_cached_trees()`
    """

    current_path = []
    top_nodes = []

    if queryset:
        # Get the model's parent-attribute name
        parent_attr = queryset[0]._mptt_meta.parent_attr
        root_level = None
        is_filtered = (hasattr(queryset, "query") and queryset.query.has_filters())
        for obj in queryset:
            # Get the current mptt node level
            node_level = obj.get_level()

            if root_level is None or (is_filtered and node_level < root_level):
                # First iteration, so set the root level to the top node level
                root_level = node_level

            elif node_level < root_level:
                # ``queryset`` was a list or other iterable (unable to order),
                # and was provided in an order other than depth-first
                raise ValueError(
                    _('Node %s not in depth-first order') % (type(queryset),)
                )

            # Set up the attribute on the node that will store cached children,
            # which is used by ``MPTTModel.get_children``
            obj._cached_children = []

            # Remove nodes not in the current branch
            while len(current_path) > node_level - root_level:
                current_path.pop(-1)

            if node_level == root_level:
                # Add the root to the list of top nodes, which will be returned
                top_nodes.append(obj)
            else:
                # Cache the parent on the current node, and attach the current
                # node to the parent's list of children
                _parent = current_path[-1]
                setattr(obj, parent_attr, _parent)
                _parent._cached_children.append(obj)

                if root_level == 0:
                    # get_ancestors() can use .parent.parent.parent...
                    setattr(obj, '_mptt_use_cached_ancestors', True)

            # Add the current node to end of the current path - the last node
            # in the current path is the parent for the next iteration, unless
            # the next iteration is higher up the tree (a new branch), in which
            # case the paths below it (e.g., this one) will be removed from the
            # current path during the next iteration
            current_path.append(obj)

    return top_nodes
