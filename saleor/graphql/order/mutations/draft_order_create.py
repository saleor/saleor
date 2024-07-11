from collections import defaultdict
from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....checkout import AddressType
from ....core.taxes import TaxError
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....discount.models import Voucher, VoucherCode
from ....discount.utils.voucher import (
    get_active_voucher_code,
    get_voucher_code_instance,
    increase_voucher_usage,
)
from ....order import OrderOrigin, OrderStatus, events, models
from ....order.error_codes import OrderErrorCode
from ....order.search import update_order_search_vector
from ....order.utils import (
    create_order_line,
    invalidate_order_prices,
    recalculate_order_weight,
    update_order_display_gross_prices,
)
from ....permission.enums import OrderPermissions
from ....shipping.utils import convert_to_shipping_method_data
from ...account.i18n import I18nMixin
from ...account.mixins import AddressMetadataMixin
from ...account.types import AddressInput
from ...app.dataloaders import get_app_promise
from ...channel.types import Channel
from ...core import ResolveInfo
from ...core.descriptions import (
    ADDED_IN_36,
    ADDED_IN_310,
    ADDED_IN_314,
    ADDED_IN_318,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import ModelWithRestrictedChannelAccessMutation
from ...core.scalars import PositiveDecimal
from ...core.types import BaseInputObjectType, NonNullList, OrderError
from ...core.utils import from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import ProductVariant
from ...shipping.utils import get_shipping_model_by_object_id
from ..types import Order
from ..utils import (
    OrderLineData,
    validate_product_is_published_in_channel,
    validate_variant_channel_listings,
)
from .utils import (
    SHIPPING_METHOD_UPDATE_FIELDS,
    ShippingMethodUpdateMixin,
    get_variant_rule_info_map,
)


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
            "by skipping the matching logic. " + ADDED_IN_36
        ),
    )
    price = PositiveDecimal(
        required=False,
        description=(
            "Custom price of the item."
            "When the line with the same variant "
            "will be provided multiple times, the last price will be used."
            + ADDED_IN_314
            + PREVIEW_FEATURE
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class DraftOrderInput(BaseInputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user = graphene.ID(
        description="Customer associated with the draft order.", name="user"
    )
    user_email = graphene.String(description="Email address of the customer.")
    discount = PositiveDecimal(description="Discount amount for the order.")
    shipping_address = AddressInput(description="Shipping address of the customer.")
    shipping_method = graphene.ID(
        description="ID of a selected shipping method.", name="shippingMethod"
    )
    voucher = graphene.ID(
        description="ID of the voucher associated with the order.",
        name="voucher",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use `voucherCode` instead.",
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
        description="External ID of this order." + ADDED_IN_310, required=False
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
    ShippingMethodUpdateMixin,
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

    @classmethod
    def get_instance_channel_id(cls, instance, **data):
        if channel_id := instance.channel_id:
            return channel_id

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
        channel_id = data.pop("channel_id", None)
        manager = get_plugin_manager_promise(info.context).get()
        shipping_method_input = {}
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
        channel = cls.clean_channel_id(info, instance, cleaned_input, channel_id)

        voucher = cleaned_input.get("voucher", None)
        voucher_code = cleaned_input.get("voucher_code", None)
        cls.clean_voucher_and_voucher_code(voucher, voucher_code)
        if "voucher" in cleaned_input:
            cls.clean_voucher(voucher, channel, cleaned_input)
        elif "voucher_code" in cleaned_input:
            cls.clean_voucher_code(voucher_code, channel, cleaned_input)

        if channel:
            cleaned_input["currency"] = channel.currency_code

        lines = data.pop("lines", None)
        cls.clean_lines(cleaned_input, lines, channel)
        cleaned_input["status"] = OrderStatus.DRAFT
        cleaned_input["origin"] = OrderOrigin.DRAFT

        cls.clean_addresses(
            info, instance, cleaned_input, shipping_address, billing_address, manager
        )

        if redirect_url:
            cls.clean_redirect_url(redirect_url)
            cleaned_input["redirect_url"] = redirect_url

        return cleaned_input

    @classmethod
    def clean_channel_id(cls, info: ResolveInfo, instance, cleaned_input, channel_id):
        if channel_id:
            if hasattr(instance, "channel"):
                raise ValidationError(
                    {
                        "channel_id": ValidationError(
                            "Can't update existing order channel id.",
                            code=OrderErrorCode.NOT_EDITABLE.value,
                        )
                    }
                )
            else:
                channel = cls.get_node_or_error(info, channel_id, only_type=Channel)
                cleaned_input["channel"] = channel
                return channel

        else:
            return instance.channel if hasattr(instance, "channel") else None

    @classmethod
    def clean_voucher_and_voucher_code(cls, voucher, voucher_code):
        if voucher and voucher_code:
            raise ValidationError(
                {
                    "voucher": ValidationError(
                        "You cannot use both a voucher and a voucher code for the same "
                        "order. Please choose one.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def clean_voucher(cls, voucher, channel, cleaned_input):
        # We need to clean voucher_code as well
        if voucher is None:
            cleaned_input["voucher_code"] = None
            return

        if isinstance(voucher, VoucherCode):
            raise ValidationError(
                {
                    "voucher": ValidationError(
                        "You cannot use voucherCode in the voucher input. "
                        "Please use voucherCode input instead with a valid voucher code.",
                        code=OrderErrorCode.INVALID_VOUCHER.value,
                    )
                }
            )

        code_instance = None
        if channel.include_draft_order_in_voucher_usage:
            # Validate voucher when it's included in voucher usage calculation
            try:
                code_instance = get_active_voucher_code(voucher, channel.slug)
            except ValidationError:
                raise ValidationError(
                    {
                        "voucher": ValidationError(
                            "Voucher is invalid.",
                            code=OrderErrorCode.INVALID_VOUCHER.value,
                        )
                    }
                )
        else:
            cls.clean_voucher_listing(voucher, channel, "voucher")
        if not code_instance:
            code_instance = voucher.codes.first()
        if code_instance:
            cleaned_input["voucher_code"] = code_instance.code
            cleaned_input["voucher_code_instance"] = code_instance

    @classmethod
    def clean_voucher_code(
        cls, voucher_code: Optional[str], channel: Channel, cleaned_input: dict
    ):
        # We need to clean voucher instance as well
        if voucher_code is None:
            cleaned_input["voucher"] = None
            return
        if channel.include_draft_order_in_voucher_usage:
            # Validate voucher when it's included in voucher usage calculation
            try:
                code_instance = get_voucher_code_instance(voucher_code, channel.slug)
            except ValidationError:
                raise ValidationError(
                    {
                        "voucher_code": ValidationError(
                            "Voucher code is invalid.",
                            code=OrderErrorCode.INVALID_VOUCHER_CODE.value,
                        )
                    }
                )
            voucher = code_instance.voucher
        else:
            code_instance = VoucherCode.objects.filter(code=voucher_code).first()
            if not code_instance:
                raise ValidationError(
                    {
                        "voucher": ValidationError(
                            "Invalid voucher code.",
                            code=OrderErrorCode.INVALID_VOUCHER_CODE.value,
                        )
                    }
                )
            voucher = code_instance.voucher
            cls.clean_voucher_listing(voucher, channel, "voucher_code")
        cleaned_input["voucher"] = voucher
        cleaned_input["voucher_code"] = voucher_code
        cleaned_input["voucher_code_instance"] = code_instance

    @classmethod
    def clean_voucher_listing(cls, voucher: "Voucher", channel: "Channel", field: str):
        if not voucher.channel_listings.filter(channel=channel).exists():
            raise ValidationError(
                {
                    field: ValidationError(
                        "Voucher not available for this order.",
                        code=OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.value,
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
        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address,
                address_type=AddressType.SHIPPING,
                instance=instance.shipping_address,
                info=info,
            )
            shipping_address = manager.change_user_address(
                shipping_address, "shipping", user=instance
            )
            cleaned_input["shipping_address"] = shipping_address
        if billing_address:
            billing_address = cls.validate_address(
                billing_address,
                address_type=AddressType.BILLING,
                instance=instance.billing_address,
                info=info,
            )
            billing_address = manager.change_user_address(
                billing_address, "billing", user=instance
            )
            cleaned_input["billing_address"] = billing_address

    @classmethod
    def clean_redirect_url(cls, redirect_url):
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            error.code = OrderErrorCode.INVALID.value
            raise ValidationError({"redirect_url": error})

    @staticmethod
    def _save_addresses(instance: models.Order, cleaned_input):
        shipping_address = cleaned_input.get("shipping_address")
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()
        billing_address = cleaned_input.get("billing_address")
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()

    @staticmethod
    def _save_lines(info, instance, lines_data, app, manager):
        if lines_data:
            lines = []
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
    def _commit_changes(
        cls, info: ResolveInfo, instance, cleaned_input, is_new_instance, app
    ):
        super().save(info, instance, cleaned_input)

        # Create draft created event if the instance is from scratch
        if is_new_instance:
            events.draft_order_created_event(
                order=instance, user=info.context.user, app=app
            )

    @classmethod
    def should_invalidate_prices(cls, cleaned_input, is_new_instance) -> bool:
        # Force price recalculation for all new instances
        return is_new_instance

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()
        return cls._save_draft_order(
            info,
            instance,
            cleaned_input,
            is_new_instance=True,
            app=app,
            manager=manager,
        )

    @classmethod
    def _save_draft_order(
        cls,
        info: ResolveInfo,
        instance,
        cleaned_input,
        *,
        is_new_instance,
        app,
        manager,
    ):
        updated_fields = []
        with traced_atomic_transaction():
            shipping_channel_listing = None
            # Process addresses
            cls._save_addresses(instance, cleaned_input)

            try:
                # Process any lines to add
                cls._save_lines(
                    info, instance, cleaned_input.get("lines_data"), app, manager
                )
            except TaxError as tax_error:
                raise ValidationError(
                    f"Unable to calculate taxes - {str(tax_error)}",
                    code=OrderErrorCode.TAX_ERROR.value,
                )

            if "shipping_method" in cleaned_input:
                method = cleaned_input["shipping_method"]
                if method is None:
                    cls.clear_shipping_method_from_order(instance)
                else:
                    shipping_channel_listing = cls.validate_shipping_channel_listing(
                        method, instance
                    )
                    shipping_method_data = convert_to_shipping_method_data(
                        method,
                        shipping_channel_listing,
                    )
                    cls.update_shipping_method(instance, method, shipping_method_data)
                    cls._update_shipping_price(instance, shipping_channel_listing)
                updated_fields.extend(SHIPPING_METHOD_UPDATE_FIELDS)

            # Save any changes create/update the draft
            cls._commit_changes(info, instance, cleaned_input, is_new_instance, app)

            if voucher := cleaned_input.get("voucher"):
                cls.handle_order_voucher(cleaned_input, instance, voucher)

            update_order_display_gross_prices(instance)

            if is_new_instance:
                cls.call_event(manager.draft_order_created, instance)

            else:
                cls.call_event(manager.draft_order_updated, instance)

            # Post-process the results
            updated_fields.extend(
                [
                    "weight",
                    "search_vector",
                    "updated_at",
                    "display_gross_prices",
                ]
            )
            if cls.should_invalidate_prices(cleaned_input, is_new_instance):
                invalidate_order_prices(instance)
                updated_fields.extend(["should_refresh_prices"])
            recalculate_order_weight(instance)
            update_order_search_vector(instance, save=False)

            instance.save(update_fields=updated_fields)

    @classmethod
    def handle_order_voucher(cls, cleaned_input, instance, voucher):
        code_instance = cleaned_input.pop("voucher_code_instance", None)
        channel = instance.channel
        if channel.include_draft_order_in_voucher_usage:
            increase_voucher_usage(
                voucher,
                code_instance,
                instance.user_email or instance.user and instance.user.email,
                increase_voucher_customer_usage=False,
            )
