from collections import defaultdict
from typing import Dict, List

import graphene
from django.core.exceptions import ValidationError
from graphene.types import InputObjectType

from ....account.models import User
from ....checkout import AddressType
from ....core.taxes import TaxError, zero_money
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
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
from ....shipping import models as shipping_models
from ....shipping.utils import convert_to_shipping_method_data
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...app.dataloaders import get_app_promise
from ...channel.types import Channel
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_36, ADDED_IN_310, PREVIEW_FEATURE
from ...core.mutations import ModelMutation
from ...core.scalars import PositiveDecimal
from ...core.types import NonNullList, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import ProductVariant
from ...shipping.utils import get_shipping_model_by_object_id
from ..types import Order
from ..utils import (
    OrderLineData,
    get_shipping_method_availability_error,
    validate_product_is_published_in_channel,
    validate_variant_channel_listings,
)


class OrderLineInput(graphene.InputObjectType):
    quantity = graphene.Int(
        description="Number of variant items ordered.", required=True
    )


class OrderLineCreateInput(OrderLineInput):
    variant_id = graphene.ID(
        description="Product variant ID.", name="variantId", required=True
    )
    force_new_line = graphene.Boolean(
        required=False,
        default_value=False,
        description=(
            "Flag that allow force splitting the same variant into multiple lines "
            "by skipping the matching logic. " + ADDED_IN_36 + PREVIEW_FEATURE
        ),
    )


class DraftOrderInput(InputObjectType):
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
        description="ID of the voucher associated with the order.", name="voucher"
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


class DraftOrderCreateInput(DraftOrderInput):
    lines = NonNullList(
        OrderLineCreateInput,
        description=(
            "Variant line input consisting of variant ID and quantity of products."
        ),
    )


class DraftOrderCreate(ModelMutation, I18nMixin):
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
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        shipping_address = data.pop("shipping_address", None)
        billing_address = data.pop("billing_address", None)
        redirect_url = data.pop("redirect_url", None)
        channel_id = data.pop("channel_id", None)
        manager = get_plugin_manager_promise(info.context).get()
        shipping_method = get_shipping_model_by_object_id(
            object_id=data.pop("shipping_method", None), raise_error=False
        )

        if email := data.get("user_email", None):
            try:
                user = User.objects.get(email=email, is_active=True)
                data["user"] = graphene.Node.to_global_id("User", user.id)
            except User.DoesNotExist:
                data["user"] = None

        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        channel = cls.clean_channel_id(info, instance, cleaned_input, channel_id)

        voucher = cleaned_input.get("voucher", None)
        if voucher:
            cls.clean_voucher(voucher, channel)

        if channel:
            cleaned_input["currency"] = channel.currency_code

        lines = data.pop("lines", None)
        cls.clean_lines(cleaned_input, lines, channel)

        cleaned_input["shipping_method"] = shipping_method
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
    def clean_voucher(cls, voucher, channel):
        if not voucher.channel_listings.filter(channel=channel).exists():
            raise ValidationError(
                {
                    "voucher": ValidationError(
                        "Voucher not available for this order.",
                        code=OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.value,
                    )
                }
            )

    @classmethod
    def clean_lines(cls, cleaned_input, lines, channel):
        if lines:
            grouped_lines_data: List[OrderLineData] = []
            lines_data_map: Dict[str, OrderLineData] = defaultdict(OrderLineData)

            variant_ids = [line.get("variant_id") for line in lines]
            variants = cls.get_nodes_or_error(variant_ids, "variants", ProductVariant)
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
                _, variant_db_id = graphene.Node.from_global_id(variant_id)
                variant = list(
                    filter(lambda x: (x.pk == int(variant_db_id)), variants)
                )[0]

                if line.get("force_new_line"):
                    line_data = OrderLineData(variant_id=variant_db_id, variant=variant)
                    grouped_lines_data.append(line_data)
                else:
                    line_data = lines_data_map[variant_db_id]
                    line_data.variant_id = variant_db_id
                    line_data.variant = variant

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
        if shipping_method := cleaned_input["shipping_method"]:
            instance.shipping_method_name = shipping_method.name
            tax_class = shipping_method.tax_class
            if tax_class:
                instance.shipping_tax_class = tax_class
                instance.shipping_tax_class_name = tax_class.name
                instance.shipping_tax_class_private_metadata = tax_class.metadata
                instance.shipping_tax_class_metadata = tax_class.private_metadata
        super().save(info, instance, cleaned_input)

        # Create draft created event if the instance is from scratch
        if is_new_instance:
            events.draft_order_created_event(
                order=instance, user=info.context.user, app=app
            )

    @classmethod
    def _update_shipping_price(
        cls,
        info: ResolveInfo,
        instance: models.Order,
        cleaned_input,
        shipping_channel_listing,
    ):
        if shipping_address := cleaned_input.get("shipping_address"):
            instance.shipping_address = shipping_address
        if (
            instance.shipping_method
            and instance.shipping_address
            and instance.is_shipping_required()
        ):
            shipping_method_data = convert_to_shipping_method_data(
                instance.shipping_method,
                shipping_channel_listing,
            )
            manager = get_plugin_manager_promise(info.context).get()
            error = get_shipping_method_availability_error(
                instance, shipping_method_data, manager
            )
            if error:
                raise ValidationError({"shipping_method": error})

            instance.base_shipping_price = shipping_channel_listing.price
        else:
            instance.base_shipping_price = zero_money(instance.currency)

    @classmethod
    def _get_shipping_channel_listing(cls, instance, cleaned_input):
        if shipping_method := cleaned_input["shipping_method"]:
            shipping_channel_listing = (
                shipping_models.ShippingMethodChannelListing.objects.filter(
                    shipping_method=shipping_method, channel__id=instance.channel_id
                ).first()
            )
            if not shipping_channel_listing:
                raise ValidationError(
                    {
                        "shipping_method": ValidationError(
                            "Shipping method not available in the given channel.",
                            code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                        )
                    }
                )
            return shipping_channel_listing
        return None

    @classmethod
    def should_invalidate_prices(cls, instance, cleaned_input, is_new_instance) -> bool:
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
        manager
    ):
        with traced_atomic_transaction():
            shipping_channel_listing = cls._get_shipping_channel_listing(
                instance, cleaned_input
            )

            # Process addresses
            cls._save_addresses(instance, cleaned_input)

            # Save any changes create/update the draft
            cls._commit_changes(info, instance, cleaned_input, is_new_instance, app)

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

            update_order_display_gross_prices(instance)

            if is_new_instance:
                cls.call_event(manager.draft_order_created, instance)

            else:
                cls.call_event(manager.draft_order_updated, instance)

            # Post-process the results
            updated_fields = [
                "weight",
                "search_vector",
                "updated_at",
                "display_gross_prices",
            ]
            if cls.should_invalidate_prices(instance, cleaned_input, is_new_instance):
                invalidate_order_prices(instance)
                cls._update_shipping_price(
                    info, instance, cleaned_input, shipping_channel_listing
                )
                updated_fields.extend(
                    ["should_refresh_prices", "base_shipping_price_amount"]
                )

            recalculate_order_weight(instance)
            update_order_search_vector(instance, save=False)

            instance.save(update_fields=updated_fields)
