from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....checkout import AddressType
from ....core.taxes import TaxError
from ....core.tracing import traced_atomic_transaction
from ....discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
    get_customer_email_for_voucher_usage,
    increase_voucher_usage,
)
from ....order import OrderOrigin, OrderStatus, events, models
from ....order.actions import call_order_event
from ....order.error_codes import OrderErrorCode
from ....order.search import update_order_search_vector
from ....order.utils import (
    create_order_line,
    invalidate_order_prices,
    recalculate_order_weight,
    update_order_display_gross_prices,
)
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...account.i18n import I18nMixin
from ...account.mixins import AddressMetadataMixin
from ...account.types import AddressInput
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.descriptions import ADDED_IN_318, ADDED_IN_321, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.enums import LanguageCodeEnum
from ...core.mutations import ModelWithRestrictedChannelAccessMutation
from ...core.scalars import PositiveDecimal
from ...core.types import BaseInputObjectType, NonNullList, OrderError
from ...core.utils import from_global_id_or_error
from ...meta.inputs import MetadataInput, MetadataInputDescription
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import ProductVariant
from ...shipping.utils import get_shipping_model_by_object_id
from ..types import Order
from ..utils import (
    OrderLineData,
    validate_product_is_published_in_channel,
    validate_variant_channel_listings,
)
from . import draft_order_cleaner
from .utils import ShippingMethodUpdateMixin, get_variant_rule_info_map, save_addresses


class OrderLineInput(BaseInputObjectType):
    quantity = graphene.Int(
        description="Number of variant items ordered.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderLineCreateInput(OrderLineInput):
    variant_id = graphene.ID(
        description="Product variant ID.", name="variantId", required=True
    )
    force_new_line = graphene.Boolean(
        required=False,
        default_value=False,
        description=(
            "Flag that allow force splitting the same variant into multiple lines "
            "by skipping the matching logic. "
        ),
    )
    price = PositiveDecimal(
        required=False,
        description=(
            "Custom price of the item."
            "When the line with the same variant "
            "will be provided multiple times, the last price will be used."
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class DraftOrderInput(BaseInputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    save_billing_address = graphene.Boolean(
        description=(
            "Indicates whether the billing address should be saved "
            "to the user’s address book upon draft order completion. "
            "Can only be set when a billing address is provided. If not specified "
            "along with the address, the default behavior is to not save the address."
        )
        + ADDED_IN_321
    )
    user = graphene.ID(
        description="Customer associated with the draft order.", name="user"
    )
    user_email = graphene.String(description="Email address of the customer.")
    discount = PositiveDecimal(
        description=(
            f"Discount amount for the order."
            f"{DEPRECATED_IN_3X_INPUT} Providing a value for the field has no effect. "
            f"Use `orderDiscountAdd` mutation instead."
        )
    )
    shipping_address = AddressInput(description="Shipping address of the customer.")
    save_shipping_address = graphene.Boolean(
        description=(
            "Indicates whether the shipping address should be saved "
            "to the user’s address book upon draft order completion."
            "Can only be set when a shipping address is provided. If not specified "
            "along with the address, the default behavior is to not save the address."
        )
        + ADDED_IN_321
    )
    shipping_method = graphene.ID(
        description="ID of a selected shipping method.", name="shippingMethod"
    )
    voucher = graphene.ID(
        description="ID of the voucher associated with the order.",
        name="voucher",
        deprecation_reason="Use `voucherCode` instead.",
    )
    voucher_code = graphene.String(
        description="A code of the voucher associated with the order." + ADDED_IN_318,
        name="voucherCode",
    )
    customer_note = graphene.String(
        description="A note from a customer. Visible by customers in the order summary."
    )
    channel_id = graphene.ID(description="ID of the channel associated with the order.")
    redirect_url = graphene.String(
        required=False,
        description=(
            "URL of a view where users should be redirected to "
            "see the order details. URL in RFC 1808 format."
        ),
    )
    external_reference = graphene.String(
        description="External ID of this order.", required=False
    )
    metadata = NonNullList(
        MetadataInput,
        description=f"Order public metadata. {ADDED_IN_321} "
        f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}",
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=f"Order private metadata. {ADDED_IN_321} "
        f"{MetadataInputDescription.PRIVATE_METADATA_INPUT}",
        required=False,
    )

    language_code = graphene.Argument(
        LanguageCodeEnum,
        required=False,
        description=(f"Order language code.{ADDED_IN_321}"),
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class DraftOrderCreateInput(DraftOrderInput):
    lines = NonNullList(
        OrderLineCreateInput,
        description=(
            "Variant line input consisting of variant ID and quantity of products."
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class DraftOrderCreate(
    AddressMetadataMixin,
    ModelWithRestrictedChannelAccessMutation,
    I18nMixin,
):
    class Arguments:
        input = DraftOrderCreateInput(
            required=True, description="Fields required to create an order."
        )

    class Meta:
        description = "Creates a new draft order."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def get_instance_channel_id(cls, instance, **data):
        channel_id = data["input"].get("channel_id")
        if not channel_id:
            raise ValidationError(
                {
                    "channel": ValidationError(
                        "Channel id is required.", code=OrderErrorCode.REQUIRED.value
                    )
                }
            )
        _, channel_id = from_global_id_or_error(
            channel_id, "Channel", raise_error=False
        )

        return channel_id

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        shipping_address = data.pop("shipping_address", None)
        billing_address = data.pop("billing_address", None)
        redirect_url = data.pop("redirect_url", None)
        shipping_method_input = {}
        manager = get_plugin_manager_promise(info.context).get()
        if "shipping_method" in data:
            shipping_method_input["shipping_method"] = get_shipping_model_by_object_id(
                object_id=data.pop("shipping_method", None),
                error_field="shipping_method",
            )

        if email := data.get("user_email", None):
            try:
                user = User.objects.get(email=email, is_active=True)
                data["user"] = graphene.Node.to_global_id("User", user.id)
            except User.DoesNotExist:
                data["user"] = None

        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        cleaned_input.update(shipping_method_input)

        # channel ID is required for draft order creation
        # if not provided get_instance_channel_id will raise a validation error
        channel = cleaned_input.pop("channel_id")
        cleaned_input["channel"] = channel

        draft_order_cleaner.clean_voucher_and_voucher_code(channel, cleaned_input)

        if channel:
            cleaned_input["currency"] = channel.currency_code

        lines = data.pop("lines", None)
        cls.clean_lines(cleaned_input, lines, channel)
        cleaned_input["status"] = OrderStatus.DRAFT
        cleaned_input["origin"] = OrderOrigin.DRAFT
        cleaned_input["lines_count"] = len(cleaned_input.get("lines_data", []))

        cls.clean_addresses(
            info, instance, cleaned_input, shipping_address, billing_address, manager
        )

        draft_order_cleaner.clean_redirect_url(redirect_url, cleaned_input)

        return cleaned_input

    @classmethod
    def clean_addresses(
        cls,
        info: ResolveInfo,
        instance,
        cleaned_input,
        shipping_address,
        billing_address,
        manager,
    ):
        save_shipping_address = cleaned_input.get("save_shipping_address")
        save_billing_address = cleaned_input.get("save_billing_address")
        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address,
                address_type=AddressType.SHIPPING,
                instance=instance.shipping_address,
                info=info,
            )
            cleaned_input["shipping_address"] = shipping_address
            cleaned_input["draft_save_shipping_address"] = (
                save_shipping_address or False
            )
        elif save_shipping_address is not None:
            raise ValidationError(
                {
                    "save_shipping_address": ValidationError(
                        "This option can only be selected if a shipping address "
                        "is provided.",
                        code=OrderErrorCode.MISSING_ADDRESS_DATA.value,
                    )
                }
            )
        if billing_address:
            billing_address = cls.validate_address(
                billing_address,
                address_type=AddressType.BILLING,
                instance=instance.billing_address,
                info=info,
            )
            cleaned_input["billing_address"] = billing_address
            cleaned_input["draft_save_billing_address"] = save_billing_address or False
        elif save_billing_address is not None:
            raise ValidationError(
                {
                    "save_billing_address": ValidationError(
                        "This option can only be selected if a billing address "
                        "is provided.",
                        code=OrderErrorCode.MISSING_ADDRESS_DATA.value,
                    )
                }
            )

    @classmethod
    def clean_lines(cls, cleaned_input, lines, channel):
        if not lines:
            return
        grouped_lines_data: list[OrderLineData] = []
        lines_data_map: dict[str, OrderLineData] = defaultdict(OrderLineData)

        variant_pks = cls.get_global_ids_or_error(
            [line.get("variant_id") for line in lines], ProductVariant, "variant_id"
        )
        variants_data = get_variant_rule_info_map(variant_pks, channel.id)
        variants = [data.variant for data in variants_data.values()]
        validate_product_is_published_in_channel(variants, channel)
        validate_variant_channel_listings(variants, channel)
        quantities = [line.get("quantity") for line in lines]
        if not all(quantity > 0 for quantity in quantities):
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Ensure this value is greater than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY.value,
                    )
                }
            )

        for line in lines:
            variant_id = line.get("variant_id")
            variant_data = variants_data[variant_id]
            variant = variant_data.variant
            custom_price = line.get("price", None)

            if line.get("force_new_line"):
                line_data = OrderLineData(
                    variant_id=variant.id,
                    variant=variant,
                    price_override=custom_price,
                    rules_info=variant_data.rules_info,
                )
                grouped_lines_data.append(line_data)
            else:
                line_data = lines_data_map[variant.id]
                line_data.variant_id = variant.id
                line_data.variant = variant
                line_data.price_override = custom_price
                line_data.rules_info = variant_data.rules_info

            if (quantity := line.get("quantity")) is not None:
                line_data.quantity += quantity

        grouped_lines_data += list(lines_data_map.values())
        cleaned_input["lines_data"] = grouped_lines_data

    @staticmethod
    def _save_lines(info, instance, lines_data, app, manager):
        lines = []
        if lines_data:
            for line_data in lines_data:
                new_line = create_order_line(
                    instance,
                    line_data,
                    manager,
                )
                lines.append(new_line)

            # New event
            events.order_added_products_event(
                order=instance,
                user=info.context.user,
                app=app,
                order_lines=lines,
            )

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input, instance_tracker=None):
        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()

        with traced_atomic_transaction():
            # Process addresses
            save_addresses(instance, cleaned_input)

            try:
                # Process any lines to add
                cls._save_lines(
                    info, instance, cleaned_input.get("lines_data"), app, manager
                )
            except TaxError as e:
                raise ValidationError(
                    f"Unable to calculate taxes - {str(e)}",
                    code=OrderErrorCode.TAX_ERROR.value,
                ) from e

            if "shipping_method" in cleaned_input:
                method = cleaned_input["shipping_method"]
                if method is None:
                    ShippingMethodUpdateMixin.clear_shipping_method_from_order(instance)
                else:
                    ShippingMethodUpdateMixin.process_shipping_method(
                        instance, method, manager, update_shipping_discount=False
                    )

            if "voucher" in cleaned_input:
                cls.handle_order_voucher(
                    cleaned_input,
                    instance,
                )

            update_order_display_gross_prices(instance)
            invalidate_order_prices(instance)
            recalculate_order_weight(instance)
            update_order_search_vector(instance, save=False)

            instance.save()

            events.draft_order_created_event(
                order=instance, user=info.context.user, app=app
            )
            call_order_event(
                manager,
                WebhookEventAsyncType.DRAFT_ORDER_CREATED,
                instance,
            )

    @classmethod
    def handle_order_voucher(
        cls,
        cleaned_input,
        instance: models.Order,
    ):
        voucher = cleaned_input["voucher"]

        # create or update voucher discount object
        create_or_update_voucher_discount_objects_for_order(instance)

        # handle voucher usage
        user_email = get_customer_email_for_voucher_usage(instance)

        channel = instance.channel
        if not channel.include_draft_order_in_voucher_usage:
            return

        if voucher:
            code_instance = cleaned_input.pop("voucher_code_instance", None)
            increase_voucher_usage(
                voucher,
                code_instance,
                user_email,
                increase_voucher_customer_usage=False,
            )

    @classmethod
    def success_response(cls, order):
        """Return a success response."""
        return DraftOrderCreate(order=SyncWebhookControlContext(order))
