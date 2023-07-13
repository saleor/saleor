import graphene
from django.core.exceptions import ValidationError

from ....menu import models
from ....menu.error_codes import MenuErrorCode
from ....permission.enums import MenuPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import MenuError, NonNullList
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_slug_and_generate_if_needed
from ...page.types import Page
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import Category, Collection
from ..types import Menu
from .menu_item_create import MenuItemInput


class MenuCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu.", required=True)
    slug = graphene.String(
        description="Slug of the menu. Will be generated if not provided.",
        required=False,
    )
    items = NonNullList(MenuItemInput, description="List of menu items.")


class MenuCreate(ModelMutation):
    class Arguments:
        input = MenuCreateInput(
            required=True, description="Fields required to create a menu."
        )

    class Meta:
        description = "Creates a new Menu."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MENU_CREATED,
                description="A menu was created.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = MenuErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        items = []
        for item in cleaned_input.get("items", []):
            category = item.get("category")
            collection = item.get("collection")
            page = item.get("page")
            url = item.get("url")
            if len([i for i in [category, collection, page, url] if i]) > 1:
                raise ValidationError(
                    {
                        "items": ValidationError(
                            "More than one item provided.",
                            code=MenuErrorCode.TOO_MANY_MENU_ITEMS.value,
                        )
                    }
                )

            if category:
                category = cls.get_node_or_error(
                    info, category, field="items", only_type=Category
                )
                item["category"] = category
            elif collection:
                collection = cls.get_node_or_error(
                    info, collection, field="items", only_type=Collection
                )
                item["collection"] = collection
            elif page:
                page = cls.get_node_or_error(info, page, field="items", only_type=Page)
                item["page"] = page
            elif not url:
                raise ValidationError(
                    {
                        "items": ValidationError(
                            "No menu item provided.",
                            code=MenuErrorCode.NO_MENU_ITEM_PROVIDED.value,
                        )
                    }
                )
            items.append(item)
        cleaned_input["items"] = items
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        items = cleaned_data.get("items", [])
        for item in items:
            instance.items.create(**item)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.menu_created, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)
