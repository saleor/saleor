"""
Form components for working with trees.
"""
from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.utils.encoding import smart_text
from django.utils.html import conditional_escape, mark_safe
from django.utils.translation import ugettext_lazy as _

from mptt.exceptions import InvalidMove
from mptt.settings import DEFAULT_LEVEL_INDICATOR


__all__ = (
    'TreeNodeChoiceField', 'TreeNodeMultipleChoiceField',
    'TreeNodePositionField', 'MoveNodeForm',
)

# Fields ######################################################################


class TreeNodeChoiceFieldMixin:
    def __init__(self, queryset, *args, **kwargs):
        self.level_indicator = kwargs.pop('level_indicator', DEFAULT_LEVEL_INDICATOR)

        # if a queryset is supplied, enforce ordering
        if hasattr(queryset, 'model'):
            mptt_opts = queryset.model._mptt_meta
            queryset = queryset.order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)

        super(TreeNodeChoiceFieldMixin, self).__init__(queryset, *args, **kwargs)

    def _get_level_indicator(self, obj):
        level = getattr(obj, obj._mptt_meta.level_attr)
        return mark_safe(conditional_escape(self.level_indicator) * level)

    def label_from_instance(self, obj):
        """
        Creates labels which represent the tree level of each node when
        generating option labels.
        """
        level_indicator = self._get_level_indicator(obj)
        return mark_safe(level_indicator + ' ' + conditional_escape(smart_text(obj)))


class TreeNodeChoiceField(TreeNodeChoiceFieldMixin, forms.ModelChoiceField):
    """A ModelChoiceField for tree nodes."""


class TreeNodeMultipleChoiceField(TreeNodeChoiceFieldMixin, forms.ModelMultipleChoiceField):
    """A ModelMultipleChoiceField for tree nodes."""


class TreeNodePositionField(forms.ChoiceField):
    """A ChoiceField for specifying position relative to another node."""
    FIRST_CHILD = 'first-child'
    LAST_CHILD = 'last-child'
    LEFT = 'left'
    RIGHT = 'right'

    DEFAULT_CHOICES = (
        (FIRST_CHILD, _('First child')),
        (LAST_CHILD, _('Last child')),
        (LEFT, _('Left sibling')),
        (RIGHT, _('Right sibling')),
    )

    def __init__(self, *args, **kwargs):
        if 'choices' not in kwargs:
            kwargs['choices'] = self.DEFAULT_CHOICES
        super(TreeNodePositionField, self).__init__(*args, **kwargs)


# Forms #######################################################################

class MoveNodeForm(forms.Form):
    """
    A form which allows the user to move a given node from one location
    in its tree to another, with optional restriction of the nodes which
    are valid target nodes for the move.
    """
    target = TreeNodeChoiceField(queryset=None)
    position = TreeNodePositionField()

    def __init__(self, node, *args, **kwargs):
        """
        The ``node`` to be moved must be provided. The following keyword
        arguments are also accepted::

        ``valid_targets``
           Specifies a ``QuerySet`` of valid targets for the move. If
           not provided, valid targets will consist of everything other
           node of the same type, apart from the node itself and any
           descendants.

           For example, if you want to restrict the node to moving
           within its own tree, pass a ``QuerySet`` containing
           everything in the node's tree except itself and its
           descendants (to prevent invalid moves) and the root node (as
           a user could choose to make the node a sibling of the root
           node).

        ``target_select_size``
           The size of the select element used for the target node.
           Defaults to ``10``.

        ``position_choices``
           A tuple of allowed position choices and their descriptions.
           Defaults to ``TreeNodePositionField.DEFAULT_CHOICES``.

        ``level_indicator``
           A string which will be used to represent a single tree level
           in the target options.
        """
        self.node = node
        valid_targets = kwargs.pop('valid_targets', None)
        target_select_size = kwargs.pop('target_select_size', 10)
        position_choices = kwargs.pop('position_choices', None)
        level_indicator = kwargs.pop('level_indicator', None)
        super(MoveNodeForm, self).__init__(*args, **kwargs)
        opts = node._mptt_meta
        if valid_targets is None:
            valid_targets = node._tree_manager.exclude(**{
                opts.tree_id_attr: getattr(node, opts.tree_id_attr),
                opts.left_attr + '__gte': getattr(node, opts.left_attr),
                opts.right_attr + '__lte': getattr(node, opts.right_attr),
            })
        self.fields['target'].queryset = valid_targets
        self.fields['target'].widget.attrs['size'] = target_select_size
        if level_indicator:
            self.fields['target'].level_indicator = level_indicator
        if position_choices:
            self.fields['position'].choices = position_choices

    def save(self):
        """
        Attempts to move the node using the selected target and
        position.

        If an invalid move is attempted, the related error message will
        be added to the form's non-field errors and the error will be
        re-raised. Callers should attempt to catch ``InvalidNode`` to
        redisplay the form with the error, should it occur.
        """
        try:
            self.node.move_to(self.cleaned_data['target'],
                              self.cleaned_data['position'])
            return self.node
        except InvalidMove as e:
            self.errors[NON_FIELD_ERRORS] = self.error_class(e)
            raise


class MPTTAdminForm(forms.ModelForm):
    """
    A form which validates that the chosen parent for a node isn't one of
    its descendants.
    """

    def __init__(self, *args, **kwargs):
        super(MPTTAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            instance = self.instance
            opts = self._meta.model._mptt_meta
            parent_field = self.fields.get(opts.parent_attr)
            if parent_field:
                parent_qs = parent_field.queryset
                parent_qs = parent_qs.exclude(
                    pk__in=instance.get_descendants(
                        include_self=True
                    ).values_list('pk', flat=True)
                )
                parent_field.queryset = parent_qs

    def clean(self):
        cleaned_data = super(MPTTAdminForm, self).clean()
        opts = self._meta.model._mptt_meta
        parent = cleaned_data.get(opts.parent_attr)
        if self.instance and parent:
            if parent.is_descendant_of(self.instance, include_self=True):
                if opts.parent_attr not in self._errors:
                    self._errors[opts.parent_attr] = self.error_class()
                self._errors[opts.parent_attr].append(_('Invalid parent'))
                del self.cleaned_data[opts.parent_attr]
        return cleaned_data
