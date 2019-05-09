"""
Template tags for working with lists of model instances which represent
trees.
"""
from django import template
from django.apps import apps
from django.db.models.fields import FieldDoesNotExist
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from mptt.utils import (drilldown_tree_for_node, get_cached_trees,
                        tree_item_iterator)

register = template.Library()


# ## ITERATIVE TAGS

class FullTreeForModelNode(template.Node):
    def __init__(self, model, context_var):
        self.model = model
        self.context_var = context_var

    def render(self, context):
        cls = apps.get_model(*self.model.split('.'))
        if cls is None:
            raise template.TemplateSyntaxError(
                _('full_tree_for_model tag was given an invalid model: %s') % self.model
            )
        context[self.context_var] = cls._tree_manager.all()
        return ''


class DrilldownTreeForNodeNode(template.Node):
    def __init__(self, node, context_var, foreign_key=None, count_attr=None,
                 cumulative=False):
        self.node = template.Variable(node)
        self.context_var = context_var
        self.foreign_key = foreign_key
        self.count_attr = count_attr
        self.cumulative = cumulative

    def render(self, context):
        # Let any VariableDoesNotExist raised bubble up
        args = [self.node.resolve(context)]

        if self.foreign_key is not None:
            app_label, model_name, fk_attr = self.foreign_key.split('.')
            cls = apps.get_model(app_label, model_name)
            if cls is None:
                raise template.TemplateSyntaxError(
                    _('drilldown_tree_for_node tag was given an invalid model: %s') %
                    '.'.join([app_label, model_name])
                )
            try:
                cls._meta.get_field(fk_attr)
            except FieldDoesNotExist:
                raise template.TemplateSyntaxError(
                    _('drilldown_tree_for_node tag was given an invalid model field: %s') % fk_attr
                )
            args.extend([cls, fk_attr, self.count_attr, self.cumulative])

        context[self.context_var] = drilldown_tree_for_node(*args)
        return ''


@register.tag
def full_tree_for_model(parser, token):
    """
    Populates a template variable with a ``QuerySet`` containing the
    full tree for a given model.

    Usage::

       {% full_tree_for_model [model] as [varname] %}

    The model is specified in ``[appname].[modelname]`` format.

    Example::

       {% full_tree_for_model tests.Genre as genres %}

    """
    bits = token.contents.split()
    if len(bits) != 4:
        raise template.TemplateSyntaxError(_('%s tag requires three arguments') % bits[0])
    if bits[2] != 'as':
        raise template.TemplateSyntaxError(_("second argument to %s tag must be 'as'") % bits[0])
    return FullTreeForModelNode(bits[1], bits[3])


@register.tag('drilldown_tree_for_node')
def do_drilldown_tree_for_node(parser, token):
    """
    Populates a template variable with the drilldown tree for a given
    node, optionally counting the number of items associated with its
    children.

    A drilldown tree consists of a node's ancestors, itself and its
    immediate children. For example, a drilldown tree for a book
    category "Personal Finance" might look something like::

       Books
          Business, Finance & Law
             Personal Finance
                Budgeting (220)
                Financial Planning (670)

    Usage::

       {% drilldown_tree_for_node [node] as [varname] %}

    Extended usage::

       {% drilldown_tree_for_node [node] as [varname] count [foreign_key] in [count_attr] %}
       {% drilldown_tree_for_node [node] as [varname] cumulative count [foreign_key] in [count_attr] %}

    The foreign key is specified in ``[appname].[modelname].[fieldname]``
    format, where ``fieldname`` is the name of a field in the specified
    model which relates it to the given node's model.

    When this form is used, a ``count_attr`` attribute on each child of
    the given node in the drilldown tree will contain a count of the
    number of items associated with it through the given foreign key.

    If cumulative is also specified, this count will be for items
    related to the child node and all of its descendants.

    Examples::

       {% drilldown_tree_for_node genre as drilldown %}
       {% drilldown_tree_for_node genre as drilldown count tests.Game.genre in game_count %}
       {% drilldown_tree_for_node genre as drilldown cumulative count tests.Game.genre in game_count %}

    """  # noqa
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits not in (4, 8, 9):
        raise template.TemplateSyntaxError(
            _('%s tag requires either three, seven or eight arguments') % bits[0])
    if bits[2] != 'as':
        raise template.TemplateSyntaxError(
            _("second argument to %s tag must be 'as'") % bits[0])
    if len_bits == 8:
        if bits[4] != 'count':
            raise template.TemplateSyntaxError(
                _("if seven arguments are given, fourth argument to %s tag must be 'with'")
                % bits[0])
        if bits[6] != 'in':
            raise template.TemplateSyntaxError(
                _("if seven arguments are given, sixth argument to %s tag must be 'in'")
                % bits[0])
        return DrilldownTreeForNodeNode(bits[1], bits[3], bits[5], bits[7])
    elif len_bits == 9:
        if bits[4] != 'cumulative':
            raise template.TemplateSyntaxError(
                _("if eight arguments are given, fourth argument to %s tag must be 'cumulative'")
                % bits[0])
        if bits[5] != 'count':
            raise template.TemplateSyntaxError(
                _("if eight arguments are given, fifth argument to %s tag must be 'count'")
                % bits[0])
        if bits[7] != 'in':
            raise template.TemplateSyntaxError(
                _("if eight arguments are given, seventh argument to %s tag must be 'in'")
                % bits[0])
        return DrilldownTreeForNodeNode(bits[1], bits[3], bits[6], bits[8], cumulative=True)
    else:
        return DrilldownTreeForNodeNode(bits[1], bits[3])


@register.filter
def tree_info(items, features=None):
    """
    Given a list of tree items, produces doubles of a tree item and a
    ``dict`` containing information about the tree structure around the
    item, with the following contents:

       new_level
          ``True`` if the current item is the start of a new level in
          the tree, ``False`` otherwise.

       closed_levels
          A list of levels which end after the current item. This will
          be an empty list if the next item is at the same level as the
          current item.

    Using this filter with unpacking in a ``{% for %}`` tag, you should
    have enough information about the tree structure to create a
    hierarchical representation of the tree.

    Example::

       {% for genre,structure in genres|tree_info %}
       {% if structure.new_level %}<ul><li>{% else %}</li><li>{% endif %}
       {{ genre.name }}
       {% for level in structure.closed_levels %}</li></ul>{% endfor %}
       {% endfor %}

    """
    kwargs = {}
    if features:
        feature_names = features.split(',')
        if 'ancestors' in feature_names:
            kwargs['ancestors'] = True
    return tree_item_iterator(items, **kwargs)


@register.filter
def tree_path(items, separator=' :: '):
    """
    Creates a tree path represented by a list of ``items`` by joining
    the items with a ``separator``.

    Each path item will be coerced to unicode, so a list of model
    instances may be given if required.

    Example::

       {{ some_list|tree_path }}
       {{ some_node.get_ancestors|tree_path:" > " }}

    """
    return separator.join(force_text(i) for i in items)


# ## RECURSIVE TAGS

@register.filter
def cache_tree_children(queryset):
    """
    Alias to `mptt.utils.get_cached_trees`.
    """

    return get_cached_trees(queryset)


class RecurseTreeNode(template.Node):
    def __init__(self, template_nodes, queryset_var):
        self.template_nodes = template_nodes
        self.queryset_var = queryset_var

    def _render_node(self, context, node):
        bits = []
        context.push()
        for child in node.get_children():
            bits.append(self._render_node(context, child))
        context['node'] = node
        context['children'] = mark_safe(''.join(bits))
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered

    def render(self, context):
        queryset = self.queryset_var.resolve(context)
        roots = cache_tree_children(queryset)
        bits = [self._render_node(context, node) for node in roots]
        return ''.join(bits)


@register.tag
def recursetree(parser, token):
    """
    Iterates over the nodes in the tree, and renders the contained block for each node.
    This tag will recursively render children into the template variable {{ children }}.
    Only one database query is required (children are cached for the whole tree)

    Usage:
            <ul>
                {% recursetree nodes %}
                    <li>
                        {{ node.name }}
                        {% if not node.is_leaf_node %}
                            <ul>
                                {{ children }}
                            </ul>
                        {% endif %}
                    </li>
                {% endrecursetree %}
            </ul>
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(_('%s tag requires a queryset') % bits[0])

    queryset_var = template.Variable(bits[1])

    template_nodes = parser.parse(('endrecursetree',))
    parser.delete_first_token()

    return RecurseTreeNode(template_nodes, queryset_var)
