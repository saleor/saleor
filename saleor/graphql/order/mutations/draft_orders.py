import graphene
from django.core.exceptions import ValidationError
from graphene.types import InputObjectType

from ....account.models import User
from ....core.exceptions import InsufficientStock
from ....core.taxes import ZERO_TAXED_MONEY
from ....order import OrderStatus, events, models
from ....order.utils import (
    add_variant_to_order,
    allocate_stock,
    change_order_line_quantity,
    delete_order_line,
    recalculate_order,
    update_order_prices,
)
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import Decimal
from ...product.types import ProductVariant
from ..types import Order, OrderLine
from ..utils import validate_draft_order


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
    discount = Decimal(description="Discount amount for the order.")
    shipping_address = AddressInput(description="Shipping address of the customer.")
    shipping_method = graphene.ID(
        description="ID of a selected shipping method.", name="shippingMethod"
    )
    voucher = graphene.ID(
        description="ID of the voucher associated with the order", name="voucher"
    )


class DraftOrderCreateInput(DraftOrderInput):
    lines = graphene.List(
        OrderLineCreateInput,
        description="""Variant line input consisting of variant ID
        and quantity of products.""",
    )


class DraftOrderCreate(ModelMutation, I18nMixin):
    class Arguments:
        input = DraftOrderCreateInput(
            required=True, description="Fields required to create an order."
        )

    class Meta:
        description = "Creates a new draft order."
        model = models.Order
        permissions = ("order.manage_orders",)

    @classmethod
    def clean_input(cls, info, instance, data):
        shipping_address = data.pop("shipping_address", None)
        billing_address = data.pop("billing_address", None)
        cleaned_input = super().clean_input(info, instance, data)

        lines = data.pop("lines", None)
        if lines:
            variant_ids = [line.get("variant_id") for line in lines]
            variants = cls.get_nodes_or_error(variant_ids, "variants", ProductVariant)
            quantities = [line.get("quantity") for line in lines]
            cleaned_input["variants"] = variants
            cleaned_input["quantities"] = quantities

        cleaned_input["status"] = OrderStatus.DRAFT
        display_gross_prices = info.context.site.settings.display_gross_prices
        cleaned_input["display_gross_prices"] = display_gross_prices

        # Set up default addresses if possible
        user = cleaned_input.get("user")
        if user and not shipping_address:
            cleaned_input["shipping_address"] = user.default_shipping_address
        if user and not billing_address:
            cleaned_input["billing_address"] = user.default_billing_address

        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address, instance=instance.shipping_address
            )
            cleaned_input["shipping_address"] = shipping_address
        if billing_address:
            billing_address = cls.validate_address(
                billing_address, instance=instance.billing_address
            )
            cleaned_input["billing_address"] = billing_address
        return cleaned_input

    @staticmethod
    def _save_addresses(info, instance: models.Order, cleaned_input):
        # Create the draft creation event
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
                    allow_overselling=True,
                    track_inventory=False,
                )

            # New event
            events.draft_order_added_products_event(
                order=instance, user=info.context.user, order_lines=lines
            )

    @classmethod
    def _commit_changes(cls, info, instance, cleaned_input):
        created = instance.pk
        super().save(info, instance, cleaned_input)

        # Create draft created event if the instance is from scratch
        if not created:
            events.draft_order_created_event(order=instance, user=info.context.user)

        instance.save(update_fields=["billing_address", "shipping_address"])

    @classmethod
    def _refresh_lines_unit_price(cls, info, instance, cleaned_input, new_instance):
        if new_instance:
            # It is a new instance, all new lines have already updated prices.
            return
        shipping_address = cleaned_input.get("shipping_address")
        if shipping_address and instance.is_shipping_required():
            update_order_prices(instance, info.context.discounts)
        billing_address = cleaned_input.get("billing_address")
        if billing_address and not instance.is_shipping_required():
            update_order_prices(instance, info.context.discounts)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        new_instance = not bool(instance.pk)

        # Process addresses
        cls._save_addresses(info, instance, cleaned_input)

        # Save any changes create/update the draft
        cls._commit_changes(info, instance, cleaned_input)

        # Process any lines to add
        cls._save_lines(
            info,
            instance,
            cleaned_input.get("quantities"),
            cleaned_input.get("variants"),
        )

        cls._refresh_lines_unit_price(info, instance, cleaned_input, new_instance)

        # Post-process the results
        recalculate_order(instance)


class DraftOrderUpdate(DraftOrderCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an order to update.")
        input = DraftOrderInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates a draft order."
        model = models.Order
        permissions = ("order.manage_orders",)


class DraftOrderDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a draft order to delete.")

    class Meta:
        description = "Deletes a draft order."
        model = models.Order
        permissions = ("order.manage_orders",)


class DraftOrderComplete(BaseMutation):
    order = graphene.Field(Order, description="Completed order.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the order that will be completed."
        )

    class Meta:
        description = "Completes creating an order."
        permissions = ("order.manage_orders",)

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
        validate_draft_order(order)
        cls.update_user_fields(order)
        order.status = OrderStatus.UNFULFILLED

        if not order.is_shipping_required():
            order.shipping_method_name = None
            order.shipping_price = ZERO_TAXED_MONEY
            if order.shipping_address:
                order.shipping_address.delete()

        order.save()

        oversold_items = []
        for line in order:
            try:
                line.variant.check_quantity(line.quantity)
                allocate_stock(line.variant, line.quantity)
            except InsufficientStock:
                allocate_stock(line.variant, line.variant.quantity_available)
                oversold_items.append(str(line))

        events.order_created_event(order=order, user=info.context.user, from_draft=True)

        if oversold_items:
            events.draft_order_oversold_items_event(
                order=order, user=info.context.user, oversold_items=oversold_items
            )

        return DraftOrderComplete(order=order)


class DraftOrderLinesCreate(BaseMutation):
    order = graphene.Field(Order, description="A related draft order.")
    order_lines = graphene.List(
        graphene.NonNull(OrderLine), description="List of newly added order lines."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the draft order to add the lines to."
        )
        input = graphene.List(
            OrderLineCreateInput,
            required=True,
            description="Fields required to add order lines.",
        )

    class Meta:
        description = "Create order lines for a draft order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        if order.status != OrderStatus.DRAFT:
            raise ValidationError({"id": "Only draft orders can be edited."})

        lines_to_add = []
        for input_line in data.get("input"):
            variant_id = input_line["variant_id"]
            variant = cls.get_node_or_error(
                info, variant_id, "variant_id", only_type=ProductVariant
            )
            quantity = input_line["quantity"]
            if quantity > 0:
                if variant:
                    lines_to_add.append((quantity, variant))
            else:
                raise ValidationError(
                    {"quantity": "Ensure this value is greater than or equal to 1."}
                )

        # Add the lines
        lines = [
            add_variant_to_order(order, variant, quantity, allow_overselling=True)
            for quantity, variant in lines_to_add
        ]

        # Create the event
        events.draft_order_added_products_event(
            order=order, user=info.context.user, order_lines=lines_to_add
        )

        recalculate_order(order)
        return DraftOrderLinesCreate(order=order, order_lines=lines)


class DraftOrderLineDelete(BaseMutation):
    order = graphene.Field(Order, description="A related draft order.")
    order_line = graphene.Field(
        OrderLine, description="An order line that was deleted."
    )

    class Arguments:
        id = graphene.ID(description="ID of the order line to delete.", required=True)

    class Meta:
        description = "Deletes an order line from a draft order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, id):
        line = cls.get_node_or_error(info, id, only_type=OrderLine)
        order = line.order
        if order.status != OrderStatus.DRAFT:
            raise ValidationError({"id": "Only draft orders can be edited."})

        db_id = line.id
        delete_order_line(line)
        line.id = db_id

        # Create the removal event
        events.draft_order_removed_products_event(
            order=order, user=info.context.user, order_lines=[(line.quantity, line)]
        )

        recalculate_order(order)
        return DraftOrderLineDelete(order=order, order_line=line)


class DraftOrderLineUpdate(ModelMutation):
    order = graphene.Field(Order, description="A related draft order.")

    class Arguments:
        id = graphene.ID(description="ID of the order line to update.", required=True)
        input = OrderLineInput(
            required=True, description="Fields required to update an order line"
        )

    class Meta:
        description = "Updates an order line of a draft order."
        model = models.OrderLine
        permissions = ("order.manage_orders",)

    @classmethod
    def clean_input(cls, info, instance, data):
        instance.old_quantity = instance.quantity
        cleaned_input = super().clean_input(info, instance, data)
        if instance.order.status != OrderStatus.DRAFT:
            raise ValidationError({"id": "Only draft orders can be edited."})

        quantity = data["quantity"]
        if quantity <= 0:
            raise ValidationError(
                {"quantity": "Ensure this value is greater than or equal to 1."}
            )
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        change_order_line_quantity(
            info.context.user, instance, instance.old_quantity, instance.quantity
        )
        recalculate_order(instance.order)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.order = instance.order
        return response
