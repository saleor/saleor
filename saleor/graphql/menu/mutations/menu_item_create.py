from typing import Type

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Model

from ....menu import models
from ....menu.error_codes import MenuErrorCode
from ....page import models as page_models
from ....permission.enums import MenuPermissions
from ....product import models as product_models
from ....webhook.event_types import WebhookEventAsyncType
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import MenuError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import MenuItem


class MenuItemInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu item.")
    url = graphene.String(description="URL of the pointed item.")
    category = graphene.ID(
        description="Category to which item points.", name="category"
    )
    collection = graphene.ID(
        description="Collection to which item points.", name="collection"
    )
    page = graphene.ID(description="Page to which item points.", name="page")


class MenuItemCreateInput(MenuItemInput):
    name = graphene.String(description="Name of the menu item.", required=True)
    menu = graphene.ID(
        description="Menu to which item belongs.", name="menu", required=True
    )
    parent = graphene.ID(
        description="ID of the parent menu. If empty, menu will be top level menu.",
        name="parent",
    )


class MenuItemCreate(ModelMutation):
    class Arguments:
        input = MenuItemCreateInput(
            required=True,
            description=(
                "Fields required to update a menu item. Only one of `url`, `category`, "
                "`page`, `collection` is allowed per item."
            ),
        )

    class Meta:
        description = "Creates a new menu item."
        model = models.MenuItem
        object_type = MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MENU_ITEM_CREATED,
                description="A menu item was created.",
            ),
        ]

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.menu_item_created, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        _validate_menu_item_instance(cleaned_input, "page", page_models.Page)
        _validate_menu_item_instance(
            cleaned_input, "collection", product_models.Collection
        )
        _validate_menu_item_instance(cleaned_input, "category", product_models.Category)

        items = [
            cleaned_input.get("page"),
            cleaned_input.get("collection"),
            cleaned_input.get("url"),
            cleaned_input.get("category"),
        ]
        items = [item for item in items if item is not None]
        if len(items) > 1:
            raise ValidationError(
                "More than one item provided.",
                code=MenuErrorCode.TOO_MANY_MENU_ITEMS.value,
            )
        return cleaned_input


def _validate_menu_item_instance(
    cleaned_input: dict, field: str, expected_model: Type[Model]
):
    """Check if the value to assign as a menu item matches the expected model."""
    item = cleaned_input.get(field)
    if item:
        if not isinstance(item, expected_model):
            msg = (
                f"Enter a valid {expected_model._meta.verbose_name} ID "
                f"(got {item._meta.verbose_name} ID)."
            )
            raise ValidationError(
                {
                    field: ValidationError(
                        msg, code=MenuErrorCode.INVALID_MENU_ITEM.value
                    )
                }
            )
