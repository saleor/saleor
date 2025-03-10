import graphene
from django.utils.text import slugify

from ....channel import models
from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ChannelPermissions
from ....tax.models import TaxConfiguration
from ....webhook.event_types import WebhookEventAsyncType
from ...account.enums import CountryCodeEnum
from ...core import ResolveInfo
from ...core.descriptions import (
    ADDED_IN_318,
    ADDED_IN_320,
    ADDED_IN_321,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
)
from ...core.doc_category import (
    DOC_CATEGORY_CHANNELS,
    DOC_CATEGORY_CHECKOUT,
    DOC_CATEGORY_ORDERS,
    DOC_CATEGORY_PAYMENTS,
    DOC_CATEGORY_PRODUCTS,
)
from ...core.mutations import DeprecatedModelMutation
from ...core.scalars import Day, Hour, Minute
from ...core.types import BaseInputObjectType, ChannelError, NonNullList
from ...core.types import common as common_types
from ...core.utils import WebhookEventInfo
from ...meta.inputs import MetadataInput
from ...plugins.dataloaders import get_plugin_manager_promise
from ..enums import (
    AllocationStrategyEnum,
    MarkAsPaidStrategyEnum,
    TransactionFlowStrategyEnum,
)
from ..types import Channel
from .utils import (
    clean_input_checkout_settings,
    clean_input_order_settings,
    clean_input_payment_settings,
)


class StockSettingsInput(BaseInputObjectType):
    allocation_strategy = AllocationStrategyEnum(
        description=(
            "Allocation strategy options. Strategy defines the preference "
            "of warehouses for allocations and reservations."
        ),
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class CheckoutSettingsInput(BaseInputObjectType):
    use_legacy_error_flow = graphene.Boolean(
        description=(
            "Default `true`. Determines if the checkout mutations should use legacy "
            "error flow. In legacy flow, all mutations can raise an exception "
            "unrelated to the requested action - (e.g. out-of-stock exception when "
            "updating checkoutShippingAddress.) "
            "If `false`, the errors will be aggregated in `checkout.problems` field. "
            "Some of the `problems` can block the finalizing checkout process. "
            "The legacy flow will be removed in Saleor 4.0. "
            "The flow with `checkout.problems` will be the default one. "
            + DEPRECATED_IN_3X_INPUT
        )
    )
    automatically_complete_fully_paid_checkouts = graphene.Boolean(
        description=(
            "Default `false`. Determines if the paid checkouts should be automatically "
            "completed. This setting applies only to checkouts where payment "
            "was processed through transactions."
            "When enabled, the checkout will be automatically completed once the "
            "checkout `charge_status` reaches `FULL`. This occurs when the total sum "
            "of charged and authorized transaction amounts equals or exceeds the "
            "checkout's total amount."
        )
        + ADDED_IN_320,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class OrderSettingsInput(BaseInputObjectType):
    automatically_confirm_all_new_orders = graphene.Boolean(
        required=False,
        description="When disabled, all new orders from checkout "
        "will be marked as unconfirmed. When enabled orders from checkout will "
        "become unfulfilled immediately. By default set to True",
    )
    automatically_fulfill_non_shippable_gift_card = graphene.Boolean(
        required=False,
        description="When enabled, all non-shippable gift card orders "
        "will be fulfilled automatically. By default set to True.",
    )
    expire_orders_after = Minute(
        required=False,
        description=(
            "Expiration time in minutes. "
            "Default null - means do not expire any orders. "
            "Enter 0 or null to disable."
        ),
    )
    delete_expired_orders_after = Day(
        required=False,
        description=(
            "The time in days after expired orders will be deleted."
            "Allowed range is from 1 to 120."
        ),
    )
    mark_as_paid_strategy = MarkAsPaidStrategyEnum(
        required=False,
        description=(
            "Determine what strategy will be used to mark the order as paid. "
            "Based on the chosen option, the proper object will be created "
            "and attached to the order when it's manually marked as paid."
            "\n`PAYMENT_FLOW` - [default option] creates the `Payment` object."
            "\n`TRANSACTION_FLOW` - creates the `TransactionItem` object."
        ),
    )
    allow_unpaid_orders = graphene.Boolean(
        required=False,
        description=(
            "Determine if it is possible to place unpaid order by calling "
            "`checkoutComplete` mutation."
        ),
    )
    include_draft_order_in_voucher_usage = graphene.Boolean(
        required=False,
        description=(
            "Specify whether a coupon applied to draft orders will count toward "
            "voucher usage."
            "\n\nWarning:  when switching this setting from `false` to `true`, "
            "the vouchers will be disconnected from all draft orders."
            + ADDED_IN_318
            + PREVIEW_FEATURE
        ),
    )
    draft_order_line_price_freeze_period = Hour(
        required=False,
        description=(
            "Time in hours after which the draft order line price will be refreshed. "
            "Default value is 24 hours. "
            "Enter 0 or null to disable." + ADDED_IN_321 + PREVIEW_FEATURE
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class PaymentSettingsInput(BaseInputObjectType):
    default_transaction_flow_strategy = TransactionFlowStrategyEnum(
        required=False,
        description=(
            "Determine the transaction flow strategy to be used. "
            "Include the selected option in the payload sent to the payment app, as a "
            "requested action for the transaction."
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class ChannelInput(BaseInputObjectType):
    is_active = graphene.Boolean(
        description="Determine if channel will be set active or not."
    )
    stock_settings = graphene.Field(
        StockSettingsInput,
        description="The channel stock settings.",
        required=False,
    )
    add_shipping_zones = NonNullList(
        graphene.ID,
        description="List of shipping zones to assign to the channel.",
        required=False,
    )
    add_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to assign to the channel.",
        required=False,
    )
    order_settings = graphene.Field(
        OrderSettingsInput,
        description="The channel order settings",
        required=False,
    )
    metadata = common_types.NonNullList(
        MetadataInput,
        description="Channel public metadata.",
        required=False,
    )
    private_metadata = common_types.NonNullList(
        MetadataInput,
        description="Channel private metadata.",
        required=False,
    )

    checkout_settings = graphene.Field(
        CheckoutSettingsInput,
        description="The channel checkout settings",
        required=False,
    )
    payment_settings = graphene.Field(
        PaymentSettingsInput,
        description="The channel payment settings",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHANNELS


class ChannelCreateInput(ChannelInput):
    name = graphene.String(description="Name of the channel.", required=True)
    slug = graphene.String(description="Slug of the channel.", required=True)
    currency_code = graphene.String(
        description="Currency of the channel.", required=True
    )
    default_country = CountryCodeEnum(
        description=(
            "Default country for the channel. Default country can be "
            "used in checkout to determine the stock quantities or calculate taxes "
            "when the country was not explicitly provided."
        ),
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHANNELS


class ChannelCreate(DeprecatedModelMutation):
    class Arguments:
        input = ChannelCreateInput(
            required=True, description="Fields required to create channel."
        )

    class Meta:
        description = "Creates new channel."
        model = models.Channel
        object_type = Channel
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHANNEL_CREATED,
                description="A channel was created.",
            ),
        ]
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def get_type_for_model(cls):
        return Channel

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        slug = cleaned_input.get("slug")
        if slug:
            cleaned_input["slug"] = slugify(slug)
        if stock_settings := cleaned_input.get("stock_settings"):
            cleaned_input["allocation_strategy"] = stock_settings["allocation_strategy"]
        if order_settings := cleaned_input.get("order_settings"):
            clean_input_order_settings(order_settings, cleaned_input, instance)

        if checkout_settings := cleaned_input.get("checkout_settings"):
            clean_input_checkout_settings(checkout_settings, cleaned_input)

        if payment_settings := cleaned_input.get("payment_settings"):
            clean_input_payment_settings(payment_settings, cleaned_input)

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            shipping_zones = cleaned_data.get("add_shipping_zones")
            if shipping_zones:
                instance.shipping_zones.add(*shipping_zones)
            warehouses = cleaned_data.get("add_warehouses")
            if warehouses:
                instance.warehouses.add(*warehouses)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        TaxConfiguration.objects.create(channel=instance)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.channel_created, instance)
