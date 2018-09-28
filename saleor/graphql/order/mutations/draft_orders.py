import graphene
from graphene.types import InputObjectType
from graphql_jwt.decorators import permission_required

from ....account.models import Address, User
from ....core.exceptions import InsufficientStock
from ....core.utils.taxes import ZERO_TAXED_MONEY
from ....order import OrderEvents, OrderStatus, models
from ....order.utils import (
    add_variant_to_order, allocate_stock, recalculate_order)
from ...account.types import AddressInput
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.types.common import Decimal, Error
from ...product.types import ProductVariant
from ..types import Order, OrderLine


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


class DraftOrderCreate(ModelMutation):
    class Arguments:
        input = DraftOrderCreateInput(
            required=True,
            description='Fields required to create an order.')

    class Meta:
        description = 'Creates a new draft order.'
        model = models.Order

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        shipping_address = input.pop('shipping_address', None)
        billing_address = input.pop('billing_address', None)
        cleaned_input = super().clean_input(info, instance, input, errors)
        lines = input.pop('lines', None)
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = cls.get_nodes_or_error(
                ids=variant_ids, only_type=ProductVariant, errors=errors,
                field='variants')
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
            shipping_address = Address(**shipping_address)
            cls.clean_instance(shipping_address, errors)
            cleaned_input['shipping_address'] = shipping_address
        if billing_address:
            billing_address = Address(**billing_address)
            cls.clean_instance(billing_address, errors)
            cleaned_input['billing_address'] = billing_address

        return cleaned_input

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.manage_orders')

    @classmethod
    def save(cls, info, instance, cleaned_input):
        shipping_address = cleaned_input.get('shipping_address')
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address
        billing_address = cleaned_input.get('billing_address')
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address
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


class DraftOrderDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a draft order to delete.')

    class Meta:
        description = 'Deletes a draft order.'
        model = models.Order

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.manage_orders')


def check_for_draft_order_errors(order, errors):
    """Return a list of errors associated with the order.

    Checks, if given order has a proper shipping address and method
    set up and return list of errors if not.
    """
    if order.get_total_quantity() == 0:
        errors.append(
            Error(
                field='lines',
                message='Could not create order without any products.'))
    if order.is_shipping_required():
        method = order.shipping_method
        shipping_address = order.shipping_address
        shipping_not_valid = (
            method and shipping_address and
            shipping_address.country.code not in method.shipping_zone.countries)  # noqa
        if shipping_not_valid:
            errors.append(
                Error(
                    field='shipping',
                    message='Shipping method is not valid for chosen shipping '
                            'address'))
    return errors


class DraftOrderComplete(BaseMutation):
    order = graphene.Field(Order, description='Completed order.')

    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of the order that will be completed.')

    class Meta:
        description = 'Completes creating an order.'

    @classmethod
    def update_user_fields(cls, order, errors):
        if order.user:
            order.user_email = order.user.email
        elif order.user_email:
            try:
                order.user = User.objects.get(email=order.user_email)
            except User.DoesNotExist:
                order.user = None
        else:
            cls.add_error(
                errors, field=None,
                message='Both user and user_email fields are null')

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id):
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        errors = check_for_draft_order_errors(order, errors)
        if errors:
            return cls(errors=errors)

        order.status = OrderStatus.UNFULFILLED
        cls.update_user_fields(order, errors)
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


class DraftOrderLineCreate(BaseMutation):
    order = graphene.Field(Order, description='A related draft order.')
    order_line = graphene.Field(
        OrderLine, description='A newly created order line.')

    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of the draft order to add the lines to.')
        input = OrderLineCreateInput(
            required=True,
            description="""
            Variant line input consisting of variant ID and quantity of
            products.""")

    class Meta:
        description = 'Create an order line for a draft order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, input):
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        variant_id = input['variant_id']
        variant = cls.get_node_or_error(
            info, variant_id, errors, 'lines', ProductVariant)

        if not (order or variant):
            return DraftOrderLineCreate(errors=errors)

        if order.status != OrderStatus.DRAFT:
            cls.add_error(
                errors, 'order_id', 'Only draft orders can be edited.')

        quantity = input['quantity']
        if quantity <= 0:
            cls.add_error(
                errors, 'quantity',
                'Ensure this value is greater than or equal to 1.')

        line = None
        if not errors:
            line = add_variant_to_order(
                order, variant, quantity, allow_overselling=True)
            recalculate_order(order)
        return DraftOrderLineCreate(
            order=order, order_line=line, errors=errors)


class DraftOrderLineDelete(BaseMutation):
    order = graphene.Field(Order, description='A related draft order.')
    order_line = graphene.Field(
        OrderLine, description='An order line that was deleted.')

    class Arguments:
        id = graphene.ID(
            description='ID of the order line to delete.', required=True)

    class Meta:
        description = 'Deletes an order line from a draft order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id):
        errors = []
        line = cls.get_node_or_error(info, id, errors, 'id', OrderLine)
        if not line:
            return DraftOrderLineDelete(errors=errors)

        order = line.order
        if order.status != OrderStatus.DRAFT:
            cls.add_error(
                errors, 'id', 'Only draft orders can be edited.')
        if not errors:
            db_id = line.id
            line.delete()
            line.id = db_id
            recalculate_order(order)
        return DraftOrderLineDelete(
            errors=errors, order=order, order_line=line)


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

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.manage_orders')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        if instance.order.status != OrderStatus.DRAFT:
            cls.add_error(
                errors, 'id', 'Only draft orders can be edited.')

        quantity = input['quantity']
        if quantity <= 0:
            cls.add_error(
                errors, 'quantity',
                'Ensure this value is greater than or equal to 1.')
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save(update_fields=['quantity'])
        recalculate_order(instance.order)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.order = instance.order
        return response
