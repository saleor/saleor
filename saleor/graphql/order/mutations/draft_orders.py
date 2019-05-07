import graphene
from django.core.exceptions import ValidationError
from graphene.types import InputObjectType

from ....account.models import User
from ....core.exceptions import InsufficientStock
from ....core.utils.taxes import ZERO_TAXED_MONEY
from ....order import OrderEvents, OrderStatus, models
from ....order.utils import (
    add_variant_to_order, allocate_stock, change_order_line_quantity,
    delete_order_line, recalculate_order)
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import Decimal
from ...product.types import ProductVariant
from ..types import Order, OrderLine
from ..utils import validate_draft_order


class OrderLineInput(graphene.InputObjectType):
    quantity = graphene.Int(
        description='Number of variant items ordered.', required=True)


class OrderLineCreateInput(OrderLineInput):
    variant_id = graphene.ID(
        description='Product variant ID.', name='variantId', required=True)


class DraftOrderInput(InputObjectType):
    billing_address = AddressInput(
        description='Billing address of the customer.')
    user = graphene.ID(
        descripton='Customer associated with the draft order.', name='user')
    user_email = graphene.String(description='Email address of the customer.')
    discount = Decimal(description='Discount amount for the order.')
    shipping_address = AddressInput(
        description='Shipping address of the customer.')
    shipping_method = graphene.ID(
        description='ID of a selected shipping method.', name='shippingMethod')
    voucher = graphene.ID(
        description='ID of the voucher associated with the order',
        name='voucher')


class DraftOrderCreateInput(DraftOrderInput):
    lines = graphene.List(
        OrderLineCreateInput,
        description="""Variant line input consisting of variant ID
        and quantity of products.""")


class DraftOrderCreate(ModelMutation, I18nMixin):
    class Arguments:
        input = DraftOrderCreateInput(
            required=True,
            description='Fields required to create an order.')

    class Meta:
        description = 'Creates a new draft order.'
        model = models.Order
        permissions = ('order.manage_orders', )

    @classmethod
    def clean_input(cls, info, instance, data):
        shipping_address = data.pop('shipping_address', None)
        billing_address = data.pop('billing_address', None)
        cleaned_input = super().clean_input(info, instance, data)

        lines = data.pop('lines', None)
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = cls.get_nodes_or_error(
                variant_ids, 'variants', ProductVariant)
            quantities = [line.get('quantity') for line in lines]
            cleaned_input['variants'] = variants
            cleaned_input['quantities'] = quantities

        cleaned_input['status'] = OrderStatus.DRAFT
        display_gross_prices = info.context.site.settings.display_gross_prices
        cleaned_input['display_gross_prices'] = display_gross_prices

        # Set up default addresses if possible
        user = cleaned_input.get('user')
        if user and not shipping_address:
            cleaned_input[
                'shipping_address'] = user.default_shipping_address
        if user and not billing_address:
            cleaned_input[
                'billing_address'] = user.default_billing_address

        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address, instance=instance.shipping_address)
            cleaned_input['shipping_address'] = shipping_address
        if billing_address:
            billing_address = cls.validate_address(
                billing_address, instance=instance.billing_address)
            cleaned_input['billing_address'] = billing_address
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        shipping_address = cleaned_input.get('shipping_address')
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()
        billing_address = cleaned_input.get('billing_address')
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()
        super().save(info, instance, cleaned_input)
        instance.save(update_fields=['billing_address', 'shipping_address'])
        variants = cleaned_input.get('variants')
        quantities = cleaned_input.get('quantities')
        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_order(
                    instance, variant, quantity, allow_overselling=True,
                    track_inventory=False)
        recalculate_order(instance)


class DraftOrderUpdate(DraftOrderCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an order to update.')
        input = DraftOrderInput(
            required=True,
            description='Fields required to update an order.')

    class Meta:
        description = 'Updates a draft order.'
        model = models.Order
        permissions = ('order.manage_orders', )


class DraftOrderDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a draft order to delete.')

    class Meta:
        description = 'Deletes a draft order.'
        model = models.Order
        permissions = ('order.manage_orders', )


class DraftOrderComplete(BaseMutation):
    order = graphene.Field(Order, description='Completed order.')

    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of the order that will be completed.')

    class Meta:
        description = 'Completes creating an order.'
        permissions = ('order.manage_orders', )

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
        if oversold_items:
            order.events.create(
                type=OrderEvents.OVERSOLD_ITEMS.value,
                user=info.context.user,
                parameters={'oversold_items': oversold_items})

        order.events.create(
            type=OrderEvents.PLACED_FROM_DRAFT.value,
            user=info.context.user)
        return DraftOrderComplete(order=order)


class DraftOrderLinesCreate(BaseMutation):
    order = graphene.Field(Order, description='A related draft order.')
    order_lines = graphene.List(
        graphene.NonNull(OrderLine),
        description='List of newly added order lines.')

    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of the draft order to add the lines to.')
        input = graphene.List(
            OrderLineCreateInput, required=True,
            description='Fields required to add order lines.')

    class Meta:
        description = 'Create order lines for a draft order.'
        permissions = ('order.manage_orders', )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get('id'), only_type=Order)
        if order.status != OrderStatus.DRAFT:
            raise ValidationError({'id': 'Only draft orders can be edited.'})

        lines = []
        for input_line in data.get('input'):
            variant_id = input_line['variant_id']
            variant = cls.get_node_or_error(
                info, variant_id, 'variant_id', only_type=ProductVariant)
            quantity = input_line['quantity']
            if quantity > 0:
                if variant:
                    line = add_variant_to_order(
                        order, variant, quantity, allow_overselling=True)
                    lines.append(line)
            else:
                raise ValidationError({
                    'quantity':
                    'Ensure this value is greater than or equal to 1.'})

        recalculate_order(order)
        return DraftOrderLinesCreate(order=order, order_lines=lines)


class DraftOrderLineDelete(BaseMutation):
    order = graphene.Field(Order, description='A related draft order.')
    order_line = graphene.Field(
        OrderLine, description='An order line that was deleted.')

    class Arguments:
        id = graphene.ID(
            description='ID of the order line to delete.', required=True)

    class Meta:
        description = 'Deletes an order line from a draft order.'
        permissions = ('order.manage_orders', )

    @classmethod
    def perform_mutation(cls, _root, info, id):
        line = cls.get_node_or_error(info, id, only_type=OrderLine)
        order = line.order
        if order.status != OrderStatus.DRAFT:
            raise ValidationError({'id': 'Only draft orders can be edited.'})

        db_id = line.id
        delete_order_line(line)
        line.id = db_id
        recalculate_order(order)
        return DraftOrderLineDelete(order=order, order_line=line)


class DraftOrderLineUpdate(ModelMutation):
    order = graphene.Field(Order, description='A related draft order.')

    class Arguments:
        id = graphene.ID(
            description='ID of the order line to update.', required=True)
        input = OrderLineInput(
            required=True,
            description='Fields required to update an order line')

    class Meta:
        description = 'Updates an order line of a draft order.'
        model = models.OrderLine
        permissions = ('order.manage_orders', )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if instance.order.status != OrderStatus.DRAFT:
            raise ValidationError({'id': 'Only draft orders can be edited.'})

        quantity = data['quantity']
        if quantity <= 0:
            raise ValidationError({
                'quantity':
                'Ensure this value is greater than or equal to 1.'})
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        change_order_line_quantity(instance, instance.quantity)
        recalculate_order(instance.order)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.order = instance.order
        return response
