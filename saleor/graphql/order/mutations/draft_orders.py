import graphene
from django.core.exceptions import ValidationError
from graphene.types import InputObjectType

from ....account.models import User
from ....checkout import AddressType
from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....core.taxes import TaxError, zero_taxed_money
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....order import OrderLineData, OrderOrigin, OrderStatus, events, models
from ....order.actions import order_created
from ....order.error_codes import OrderErrorCode
from ....order.utils import (
    add_variant_to_order,
    get_order_country,
    recalculate_order,
    update_order_prices,
)
from ....warehouse.management import allocate_stocks
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...channel.types import Channel
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import PositiveDecimal
from ...core.types.common import OrderError
from ...product.types import ProductVariant
from ..types import Order
from ..utils import (
    prepare_insufficient_stock_order_validation_errors,
    validate_draft_order,
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


class DraftOrderInput(InputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user = graphene.ID(
        descripton="Customer associated with the draft order.", name="user"
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


class DraftOrderCreateInput(DraftOrderInput):
    lines = graphene.List(
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
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        shipping_address = data.pop("shipping_address", None)
        billing_address = data.pop("billing_address", None)
        redirect_url = data.pop("redirect_url", None)
        channel_id = data.pop("channel_id", None)

        cleaned_input = super().clean_input(info, instance, data)

        channel = cls.clean_channel_id(info, instance, cleaned_input, channel_id)

        voucher = cleaned_input.get("voucher", None)
        if voucher:
            cls.clean_voucher(voucher, channel)

        if channel:
            cleaned_input["currency"] = channel.currency_code

        lines = data.pop("lines", None)
        cls.clean_lines(cleaned_input, lines, channel)

        cleaned_input["status"] = OrderStatus.DRAFT
        cleaned_input["origin"] = OrderOrigin.DRAFT
        display_gross_prices = info.context.site.settings.display_gross_prices
        cleaned_input["display_gross_prices"] = display_gross_prices

        cls.clean_addresses(
            info, instance, cleaned_input, shipping_address, billing_address
        )

        if redirect_url:
            cls.clean_redirect_url(redirect_url)
            cleaned_input["redirect_url"] = redirect_url

        return cleaned_input

    @classmethod
    def clean_channel_id(cls, info, instance, cleaned_input, channel_id):
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
                            code=OrderErrorCode.ZERO_QUANTITY,
                        )
                    }
                )
            cleaned_input["variants"] = variants
            cleaned_input["quantities"] = quantities

    @classmethod
    def clean_addresses(
        cls, info, instance, cleaned_input, shipping_address, billing_address
    ):
        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address,
                address_type=AddressType.SHIPPING,
                instance=instance.shipping_address,
                info=info,
            )
            shipping_address = info.context.plugins.change_user_address(
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
            billing_address = info.context.plugins.change_user_address(
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
    def _save_addresses(info, instance: models.Order, cleaned_input):
        shipping_address = cleaned_input.get("shipping_address")
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()
        billing_address = cleaned_input.get("billing_address")
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()

    @staticmethod
    def _save_lines(info, instance, quantities, variants):
        if variants and quantities:
            lines = []
            for variant, quantity in zip(variants, quantities):
                lines.append((quantity, variant))
                add_variant_to_order(
                    instance,
                    variant,
                    quantity,
                    info.context.user,
                    info.context.app,
                    info.context.plugins,
                )

            # New event
            events.order_added_products_event(
                order=instance,
                user=info.context.user,
                app=info.context.app,
                order_lines=lines,
            )

    @classmethod
    def _commit_changes(cls, info, instance, cleaned_input):
        created = instance.pk
        super().save(info, instance, cleaned_input)

        # Create draft created event if the instance is from scratch
        if not created:
            events.draft_order_created_event(
                order=instance, user=info.context.user, app=info.context.app
            )

        instance.save(update_fields=["billing_address", "shipping_address"])

    @classmethod
    def _refresh_lines_unit_price(cls, info, instance, cleaned_input, new_instance):
        if new_instance:
            # It is a new instance, all new lines have already updated prices.
            return
        shipping_address = cleaned_input.get("shipping_address")
        if shipping_address and instance.is_shipping_required():
            update_order_prices(
                instance,
                info.context.plugins,
                info.context.site.settings.include_taxes_in_prices,
            )
        billing_address = cleaned_input.get("billing_address")
        if billing_address and not instance.is_shipping_required():
            update_order_prices(
                instance,
                info.context.plugins,
                info.context.site.settings.include_taxes_in_prices,
            )

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):
        new_instance = not bool(instance.pk)

        # Process addresses
        cls._save_addresses(info, instance, cleaned_input)

        # Save any changes create/update the draft
        cls._commit_changes(info, instance, cleaned_input)

        try:
            # Process any lines to add
            cls._save_lines(
                info,
                instance,
                cleaned_input.get("quantities"),
                cleaned_input.get("variants"),
            )

            cls._refresh_lines_unit_price(info, instance, cleaned_input, new_instance)
        except TaxError as tax_error:
            raise ValidationError(
                "Unable to calculate taxes - %s" % str(tax_error),
                code=OrderErrorCode.TAX_ERROR.value,
            )

        # Post-process the results
        recalculate_order(instance)


class DraftOrderUpdate(DraftOrderCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a draft order to update.")
        input = DraftOrderInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates a draft order."
        model = models.Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(
            info, qs=models.Order.objects.prefetch_related("lines"), **data
        )
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to non-draft order. "
                        "Use `orderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )
        return instance


class DraftOrderDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a draft order to delete.")

    class Meta:
        description = "Deletes a draft order."
        model = models.Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"


class DraftOrderComplete(BaseMutation):
    order = graphene.Field(Order, description="Completed order.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the order that will be completed."
        )

    class Meta:
        description = "Completes creating an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def update_user_fields(cls, order):
        if order.user:
            order.user_email = order.user.email
        elif order.user_email:
            try:
                order.user = User.objects.get(email=order.user_email)
            except User.DoesNotExist:
                order.user = None

    @classmethod
    def perform_mutation(cls, _root, info, id):
        order = cls.get_node_or_error(info, id, only_type=Order)
        country = get_order_country(order)
        validate_draft_order(order, country)
        cls.update_user_fields(order)
        order.status = OrderStatus.UNFULFILLED

        if not order.is_shipping_required():
            order.shipping_method_name = None
            order.shipping_price = zero_taxed_money(order.currency)
            if order.shipping_address:
                order.shipping_address.delete()
                order.shipping_address = None

        order.save()

        for line in order.lines.all():
            if line.variant.track_inventory:
                line_data = OrderLineData(
                    line=line, quantity=line.quantity, variant=line.variant
                )
                try:
                    allocate_stocks([line_data], country, order.channel.slug)
                except InsufficientStock as exc:
                    errors = prepare_insufficient_stock_order_validation_errors(exc)
                    raise ValidationError({"lines": errors})
        order_created(
            order,
            user=info.context.user,
            app=info.context.app,
            manager=info.context.plugins,
            from_draft=True,
        )

        return DraftOrderComplete(order=order)
