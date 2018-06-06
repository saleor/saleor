import graphene

from .types import Menu, MenuItem
from .forms import MenuForm
from ..utils import get_nodes
from ..core.mutations import (
    StaffMemberRequiredMixin, ModelFormMutation, ModelFormUpdateMutation)

class MenuCreate(StaffMemberRequiredMixin, ModelFormMutation):
    permissions = 'menu.edit_menu'

    class Input:
        items = graphene.List(
            graphene.ID, required=False, description='List of menu items IDs.')

    class Meta:
        description = 'Creates a new menu.'
        form_class = MenuForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        item_ids = input.pop('items', None)
        kwargs = super().get_form_kwargs(root, info, **input)
        if item_ids:
            items = set(get_nodes(item_ids, MenuItem))
            kwargs['data']['items'] = items
        return kwargs

    @classmethod
    def save(cls, root, info, **kwargs):
        instance = super().save(root, info, **kwargs)
        if instance:
            kwargs = cls.get_form_kwargs(root, info, **kwargs)
            items = kwargs['data'].get('items')
            if items:
                instance.items.add(*items)
                instance.save()
            return instance
