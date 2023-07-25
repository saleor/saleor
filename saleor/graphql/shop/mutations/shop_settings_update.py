import graphene
from django.core.exceptions import ValidationError

from ....core.error_codes import ShopErrorCode
from ....core.utils.url import validate_storefront_url
from ....permission.enums import SitePermissions
from ....site.models import DEFAULT_LIMIT_QUANTITY_PER_CHECKOUT
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_314,
    ADDED_IN_315,
    DEPRECATED_IN_3X_INPUT,
)
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.enums import WeightUnitsEnum
from ...core.mutations import BaseMutation
from ...core.types import ShopError
from ...core.types import common as common_types
from ...core.utils import WebhookEventInfo
from ...meta.inputs import MetadataInput
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ..types import Shop


class ShopSettingsInput(graphene.InputObjectType):
    header_text = graphene.String(description="Header text.")
    description = graphene.String(description="SEO description.")
    track_inventory_by_default = graphene.Boolean(
        description=(
            "This field is used as a default value for "
            "`ProductVariant.trackInventory`."
        )
    )
    default_weight_unit = WeightUnitsEnum(description="Default weight unit.")
    automatic_fulfillment_digital_products = graphene.Boolean(
        description="Enable automatic fulfillment for all digital products."
    )
    fulfillment_auto_approve = graphene.Boolean(
        description="Enable automatic approval of all new fulfillments." + ADDED_IN_31
    )
    fulfillment_allow_unpaid = graphene.Boolean(
        description=(
            "Enable ability to approve fulfillments which are unpaid." + ADDED_IN_31
        )
    )
    default_digital_max_downloads = graphene.Int(
        description="Default number of max downloads per digital content URL."
    )
    default_digital_url_valid_days = graphene.Int(
        description="Default number of days which digital content URL will be valid."
    )
    default_mail_sender_name = graphene.String(
        description="Default email sender's name."
    )
    default_mail_sender_address = graphene.String(
        description="Default email sender's address."
    )
    customer_set_password_url = graphene.String(
        description="URL of a view where customers can set their password."
    )
    reserve_stock_duration_anonymous_user = graphene.Int(
        description=(
            "Default number of minutes stock will be reserved for "
            "anonymous checkout. Enter 0 or null to disable." + ADDED_IN_31
        )
    )
    reserve_stock_duration_authenticated_user = graphene.Int(
        description=(
            "Default number of minutes stock will be reserved for "
            "authenticated checkout. Enter 0 or null to disable." + ADDED_IN_31
        )
    )
    limit_quantity_per_checkout = graphene.Int(
        description=(
            "Default number of maximum line quantity "
            "in single checkout. Minimum possible value is 1, default "
            f"value is {DEFAULT_LIMIT_QUANTITY_PER_CHECKOUT}." + ADDED_IN_31
        )
    )

    enable_account_confirmation_by_email = graphene.Boolean(
        description="Enable automatic account confirmation by email." + ADDED_IN_314
    )
    allow_login_without_confirmation = graphene.Boolean(
        description=(
            "Enable possibility to login without account confirmation." + ADDED_IN_315
        )
    )
    metadata = common_types.NonNullList(
        MetadataInput,
        description="Shop public metadata." + ADDED_IN_315,
        required=False,
    )
    private_metadata = common_types.NonNullList(
        MetadataInput,
        description="Shop private metadata." + ADDED_IN_315,
        required=False,
    )
    # deprecated
    include_taxes_in_prices = graphene.Boolean(
        description=(
            f"Include taxes in prices. {DEPRECATED_IN_3X_INPUT} Use "
            "`taxConfigurationUpdate` mutation to configure this setting per channel "
            "or country."
        )
    )
    display_gross_prices = graphene.Boolean(
        description=(
            f"Display prices with tax in store. {DEPRECATED_IN_3X_INPUT} Use "
            "`taxConfigurationUpdate` mutation to configure this setting per channel "
            "or country."
        )
    )
    charge_taxes_on_shipping = graphene.Boolean(
        description=(
            f"Charge taxes on shipping. {DEPRECATED_IN_3X_INPUT} To enable taxes for "
            "a shipping method, assign a tax class to the shipping method with "
            "`shippingPriceCreate` or `shippingPriceUpdate` mutations."
        ),
    )


class ShopSettingsUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = ShopSettingsInput(
            description="Fields required to update shop settings.", required=True
        )

    class Meta:
        description = "Updates shop settings."
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"
        support_meta_field = True
        support_private_meta_field = True
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SHOP_METADATA_UPDATED,
                description=(
                    "Optionally triggered when public or private metadata is updated."
                ),
            ),
        ]

    @classmethod
    def clean_input(cls, _info, _instance, data):
        if data.get("customer_set_password_url"):
            try:
                validate_storefront_url(data["customer_set_password_url"])
            except ValidationError as error:
                raise ValidationError(
                    {"customer_set_password_url": error},
                    code=ShopErrorCode.INVALID.value,
                )

        if "reserve_stock_duration_anonymous_user" in data:
            new_value = data["reserve_stock_duration_anonymous_user"]
            if not new_value or new_value < 1:
                data["reserve_stock_duration_anonymous_user"] = None
        if "reserve_stock_duration_authenticated_user" in data:
            new_value = data["reserve_stock_duration_authenticated_user"]
            if not new_value or new_value < 1:
                data["reserve_stock_duration_authenticated_user"] = None
        if "limit_quantity_per_checkout" in data:
            new_value = data["limit_quantity_per_checkout"]
            if new_value is not None and new_value < 1:
                raise ValidationError(
                    {
                        "limit_quantity_per_checkout": ValidationError(
                            "Quantity limit cannot be lower than 1.",
                            code=ShopErrorCode.INVALID.value,
                        )
                    }
                )
            if not new_value:
                data["limit_quantity_per_checkout"] = None

        return data

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        for field_name, desired_value in cleaned_data.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)
        return instance

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        instance = site.settings
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)

        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)
        old_metadata = dict(instance.metadata)
        old_private_metadata = dict(instance.private_metadata)

        instance = cls.construct_instance(instance, cleaned_input)
        cls.validate_and_update_metadata(instance, metadata_list, private_metadata_list)
        cls.clean_instance(info, instance)
        instance.save()

        if (
            instance.metadata != old_metadata
            or instance.private_metadata != old_private_metadata
        ):
            manager = get_plugin_manager_promise(info.context).get()
            manager.shop_metadata_updated(instance)

        return ShopSettingsUpdate(shop=Shop())
