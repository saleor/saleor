import graphene
from django.utils.translation import npgettext_lazy, pgettext_lazy
from graphene.types import InputObjectType
from graphql_jwt.decorators import permission_required
from payments import PaymentError, PaymentStatus

from ...account.models import Address
from ...core.exceptions import InsufficientStock
from ...core.utils.taxes import ZERO_TAXED_MONEY
from ...order import CustomPaymentChoices, OrderStatus, models
from ...order.utils import (
    add_variant_to_order, cancel_fulfillment, cancel_order, recalculate_order)
from ...shipping.models import ANY_COUNTRY
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import Decimal, Error
from ..product.types import ProductVariant
from ..utils import get_node, get_nodes
from .types import Fulfillment, Order


def try_payment_action(action, money, errors):
    try:
        action(money)
    except (PaymentError, ValueError) as e:
        errors.append(Error(field='payment', message=str(e)))


class AddressInput(graphene.InputObjectType):
    first_name = graphene.String(description='Given name.')
    last_name = graphene.String(description='Family name.')
    company_name = graphene.String(description='Company or organization.')
    street_address_1 = graphene.String(description='Address.')
    street_address_2 = graphene.String(description='Address.')
    city = graphene.String(description='City.')
    city_area = graphene.String(description='District.')
    postal_code = graphene.String(description='Postal code.')
    country = graphene.String(description='Country.')
    country_area = graphene.String(description='State or province.')
    phone = graphene.String(description='Phone number.')


class LineInput(graphene.InputObjectType):
    variant_id = graphene.ID(description='Product variant ID.')
    quantity = graphene.Int(
        description='The number of products in the order.')

    class Meta:
        description = 'Represents a permission object in a friendly form.'

class DraftOrderInput(InputObjectType):
    billing_address = AddressInput(
        description='Address associated with the payment.')
    user = graphene.ID(
        descripton='Customer associated with the draft order.')
    user_email = graphene.String(description='Email address of the customer.')
    discount = Decimal(description='Discount amount for the order.')
    lines = graphene.List(
        LineInput,
        description="""Variant line input consisting of variant ID 
        and quantity of products.""")
    shipping_address = AddressInput(
        description='Address to where the order will be shipped.')
    shipping_method = graphene.ID(
        description='ID of a selected shipping method.')
    voucher = graphene.ID(
        description='ID of the voucher associated with the order')


class OrderUpdateInput(graphene.InputObjectType):
    billing_address = AddressInput(
        description='Address associated with the payment.')
    user_email = graphene.String(description='Email address of the customer.')
    shipping_address = AddressInput(
        description='Address to where the order will be shipped.')


def check_lines_quantity(variants, quantities):
    """Check if stock is sufficient for each line in the list of dicts.

    Return list of errors.
    """
    errors = []

    for variant, quantity in zip(variants, quantities):
        try:
            variant.check_quantity(quantity)
        except InsufficientStock as e:
            message = pgettext_lazy(
                'Add line mutation error',
                'Could not add item. Only %(remaining)d remaining in stock.' %
                {'remaining': e.item.quantity_available})
            errors.append((variant.sku, message))
    return errors


class DraftOrderCreate(ModelMutation):
    class Arguments:
        input = DraftOrderInput(
            required=True,
            description='Fields required to create an order.')

    class Meta:
        description = 'Creates a new variant for a product.'
        model = models.Order

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        shipping_address = input.pop('shipping_address', None)
        billing_address = input.pop('billing_address', None)
        cleaned_input = super().clean_input(info, instance, input, errors)
        lines = input.pop('lines', None)
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = get_nodes(ids=variant_ids, graphene_type=ProductVariant)
            quantities = [line.get('quantity') for line in lines]
            line_errors = check_lines_quantity(variants, quantities)
            if line_errors:
                for err in line_errors:
                    cls.add_error(errors, field=err[0], message=err[1])
            else:
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
        return user.has_perm('order.edit_order')

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
                add_variant_to_order(instance, variant, quantity)
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
        return user.has_perm('order.edit_order')


def check_for_draft_order_errors(order):
    """Return a list of errors associated with the order.

    Checks, if given order has a proper shipping address and method
    set up and return list of errors if not.
    """
    errors = []
    if order.get_total_quantity() == 0:
        errors.append(
            Error(
                field='lines',
                message='Could not create order without any products.'))
    method = order.shipping_method
    shipping_address = order.shipping_address
    shipping_not_valid = (
        method and shipping_address and
        method.country_code != ANY_COUNTRY and
        shipping_address.country.code != method.country_code)
    if shipping_not_valid:
        errors.append(
            Error(
                field='shipping',
                message='Shipping method is not valid for chosen shipping '
                        'address'))
    return errors


class DraftOrderComplete(BaseMutation):
    class Arguments:
        order_id = graphene.ID(
            required=True,
            description='ID of the order that will be completed.')

    class Meta:
        description = 'Completes creating an order.'

    order = graphene.Field(
        Order, description='Completed order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, order_id):
        order = get_node(info, order_id, only_type=Order)
        errors = check_for_draft_order_errors(order)
        if errors:
            return cls(errors=errors)

        order.status = OrderStatus.UNFULFILLED
        if order.user:
            order.user_email = order.user.email
        remove_shipping_address = False
        if not order.is_shipping_required():
            order.shipping_method_name = None
            order.shipping_price = ZERO_TAXED_MONEY
            if order.shipping_address:
                remove_shipping_address = True
        order.save()
        if remove_shipping_address:
            order.shipping_address.delete()
        msg = 'Order created from draft order'
        order.history.create(content=msg, user=info.context.user)
        return DraftOrderComplete(order=order)


class OrderUpdate(DraftOrderUpdate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an order to update.')
        input = OrderUpdateInput(
            required=True,
            description='Fields required to update an order.')

    class Meta:
        description = 'Updates an order.'
        model = models.Order


class OrderAddNoteInput(graphene.InputObjectType):
    order = graphene.ID(description='ID of the order.')
    user = graphene.ID(description='ID of the user who added note.')
    content = graphene.String(description='Note content.')
    is_public = graphene.String(
        description='Determine if note is visible by customer or not.')


class OrderAddNote(ModelMutation):
    class Arguments:
        input = OrderAddNoteInput(
            required=True,
            description='Fields required to add note to order.')

    class Meta:
        description = 'Adds note to order.'
        model = models.OrderNote

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.edit_order')

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super.save(info, instance, cleaned_input)
        msg = 'Added note'
        instance.order.history.create(content=msg, user=info.context.user)


class OrderCancel(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to cancel.')
        restock = graphene.Boolean(
            required=True,
            description='Determine if lines will be restocked or not.')

    order = graphene.Field(
        Order, description='Canceled order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id, restock):
        order = get_node(info, id, only_type=Order)
        cancel_order(order=order, restock=restock)
        if restock:
            restock_msg = npgettext_lazy(
                'Dashboard message',
                'Restocked %(quantity)d item',
                'Restocked %(quantity)d items',
                'quantity') % {'quantity': order.get_total_quantity()}
            order.history.create(content=restock_msg, user=info.context.user)
        else:
            msg = pgettext_lazy('Dashboard message', 'Order canceled')
            order.history.create(content=msg, user=info.context.user)
        return OrderCancel(order=order)


class OrderMarkAsPaid(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to mark paid.')

    order = graphene.Field(
        Order, description='Mark order as manually paid.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id):
        order = get_node(info, id, only_type=Order)
        if order.payments.exists():
            field = 'payment'
            msg = 'Orders with payments can not be manually marked as paid.'
            return cls(errors=[Error(field=field, message=msg)])
        defaults = {
            'total': order.total.gross.amount,
            'tax': order.total.tax.amount,
            'currency': order.total.currency,
            'delivery': order.shipping_price.net.amount,
            'description': pgettext_lazy(
                'Payment description', 'Order %(order)s') % {'order': order},
            'captured_amount': order.total.gross.amount}
        models.Payment.objects.get_or_create(
            variant=CustomPaymentChoices.MANUAL,
            status=PaymentStatus.CONFIRMED, order=order,
            defaults=defaults)
        msg = 'Order manually marked as paid.'
        order.history.create(content=msg, user=info.context.user)
        return OrderMarkAsPaid(order=order)


class OrderCapture(BaseMutation):
    class Arguments:
        order_id = graphene.ID(
            required=True, description='ID of the order to capture.')
        amount = Decimal(
            required=True, description='Amount of money to capture.')

    order = graphene.Field(
        Order, description='Captured order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, order_id, amount):
        order = get_node(info, order_id, only_type=Order)
        payment = order.get_last_payment()
        errors = []
        try_payment_action(payment.capture, amount, errors)
        if errors:
            return cls(errors=errors)

        msg = 'Captured %(amount)s' % {'amount': amount}
        order.history.create(content=msg, user=info.context.user)
        return OrderCapture(order=order)


class OrderRelease(BaseMutation):
    class Arguments:
        order_id = graphene.ID(
            required=True, description='ID of the order to release.')

    order = graphene.Field(
        Order, description='released order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, order_id):
        order = get_node(info, order_id, only_type=Order)
        payment = order.get_last_payment()
        errors = []
        if payment.status != PaymentStatus.PREAUTH:
            errors.append(
                Error(field='payment',
                      message='Only pre-authorized payments can be released'))
        try:
            payment.release()
        except (PaymentError, ValueError) as e:
            errors.append(Error(field='payment', message=str(e)))
        if errors:
            return cls(errors=errors)

        msg = 'Released payment'
        order.history.create(content=msg, user=info.context.user)
        return OrderRelease(order=order)


class OrderRefund(BaseMutation):
    class Arguments:
        order_id = graphene.ID(
            required=True, description='ID of the order to refund.')
        amount = Decimal(
            required=True, description='Amount of money to refund.')

    order = graphene.Field(
        Order, description='released order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, order_id, amount):
        order = get_node(info, order_id, only_type=Order)
        payment = order.get_last_payment()
        errors = []
        if payment.variant == CustomPaymentChoices.MANUAL:
            errors.append(
                Error(field='payment',
                      message='Manual payments can not be refunded.'))
        try_payment_action(payment.refund, amount, errors)
        if errors:
            return cls(errors=errors)

        msg = 'Refunded %(amount)s' % {'amount': amount}
        order.history.create(content=msg, user=info.context.user)
        return OrderRefund(order=order)


class FulfillmentLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(description='The ID of the order line.')
    quantity = graphene.Int(
        description='The number of line item(s) to be fullfiled.')


class FulfillmentCreateInput(graphene.InputObjectType):
    order = graphene.ID(description='ID of the order to be fulfilled.')
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(description='Is customer notified.')
    lines = graphene.List(
        FulfillmentLineInput, description='Item line to be fulfilled.')


class FulfillmentUpdateInput(graphene.InputObjectType):
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(description='Is customer notified.')


class FulfillmentCancelInput(graphene.InputObjectType):
    restock = graphene.Boolean(description='Whether item lines are restocked.')


class FulfillmentCreate(ModelMutation):
    class Arguments:
        input = FulfillmentCreateInput(
            required=True,
            description='Fields required to create an fulfillment.')

    class Meta:
        description = 'Creates a new fulfillment for an order.'
        model = models.Fulfillment


class FulfillmentUpdate(FulfillmentCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an fulfillment to update.')
        input = FulfillmentUpdateInput(
            required=True,
            description='Fields required to update an fulfillment.')

    class Meta:
        description = 'Updates a fulfillment for an order.'
        model = models.Fulfillment


class FulfillmentCancel(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an fulfillment to cancel.')
        input = FulfillmentCancelInput(
            required=True,
            description='Fields required to cancel an fulfillment.')

    fulfillment = graphene.Field(
        Fulfillment, description='released fulfillment.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id, input):
        restock = input.get('restock')
        fulfillment = get_node(info, id, only_type=Fulfillment)
        order = fulfillment.order
        errors = []
        if not fulfillment.can_edit():
            errors.append(
                Error(
                    field='fulfillment',
                    message=pgettext_lazy(
                        'Cancel fulfillment mutation error',
                        'This fulfillment can\'t be canceled')))
        if errors:
            return cls(errors=errors)
        cancel_fulfillment(fulfillment, restock)
        if restock:
            msg = npgettext_lazy(
                'Dashboard message',
                'Restocked %(quantity)d item',
                'Restocked %(quantity)d items',
                'quantity') % {'quantity': fulfillment.get_total_quantity()}
        else:
            msg = pgettext_lazy(
                'Dashboard message',
                'Fulfillment #%(fulfillment)s canceled') % {
                    'fulfillment': fulfillment.composed_id}
        order.history.create(content=msg, user=info.context.user)
        return FulfillmentCancel(fulfillment=fulfillment)
