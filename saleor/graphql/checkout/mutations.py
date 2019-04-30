from datetime import date

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from ...checkout import models
from ...checkout.utils import (
    add_variant_to_checkout, add_voucher_to_checkout,
    change_billing_address_in_checkout, change_shipping_address_in_checkout,
    clean_checkout, create_order, get_or_create_user_checkout,
    get_taxes_for_checkout, get_voucher_for_checkout,
    recalculate_checkout_discount, remove_voucher_from_checkout)
from ...core import analytics
from ...core.exceptions import InsufficientStock
from ...core.utils.taxes import get_taxes_for_address
from ...discount import models as voucher_model
from ...order import OrderEvents, OrderEventsEmails
from ...order.emails import send_order_confirmation
from ...payment import PaymentError
from ...payment.utils import gateway_process_payment
from ...shipping.models import ShippingMethod as ShippingMethodModel
from ..account.i18n import I18nMixin
from ..account.types import AddressInput, User
from ..core.mutations import BaseMutation, ModelMutation
from ..core.utils import from_global_id_strict_type
from ..order.types import Order
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from .types import Checkout, CheckoutLine


def clean_shipping_method(
        checkout, method, discounts, taxes, country_code=None, remove=True):
    # FIXME Add tests for this function
    if not method:
        return None

    if not checkout.is_shipping_required():
        raise ValidationError('This checkout does not requires shipping.')

    if not checkout.shipping_address:
        raise ValidationError(
            'Cannot choose a shipping method for a checkout without the '
            'shipping address.')

    valid_methods = (
        ShippingMethodModel.objects.applicable_shipping_methods(
            price=checkout.get_subtotal(discounts, taxes).gross.amount,
            weight=checkout.get_total_weight(),
            country_code=country_code or checkout.shipping_address.country.code
        ))
    valid_methods = valid_methods.values_list('id', flat=True)

    if method.pk not in valid_methods and not remove:
        raise ValidationError(
            'Shipping method cannot be used with this checkout.')

    if remove:
        checkout.shipping_method = None
        checkout.save(update_fields=['shipping_method'])


def check_lines_quantity(variants, quantities):
    """Check if stock is sufficient for each line in the list of dicts."""
    for variant, quantity in zip(variants, quantities):
        if quantity > settings.MAX_CHECKOUT_LINE_QUANTITY:
            raise ValidationError({
                'quantity': 'Cannot add more than %d times this item.'
                            '' % settings.MAX_CHECKOUT_LINE_QUANTITY})
        try:
            variant.check_quantity(quantity)
        except InsufficientStock as e:
            message = (
                'Could not add item '
                + '%(item_name)s. Only %(remaining)d remaining in stock.' % {
                    'remaining': e.item.quantity_available,
                    'item_name': e.item.display_product()})
            raise ValidationError({'quantity': message})


class CheckoutLineInput(graphene.InputObjectType):
    quantity = graphene.Int(
        required=True, description='The number of items purchased.')
    variant_id = graphene.ID(
        required=True, description='ID of the ProductVariant.')


class CheckoutCreateInput(graphene.InputObjectType):
    lines = graphene.List(
        CheckoutLineInput,
        description=(
            'A list of checkout lines, each containing information about '
            'an item in the checkout.'), required=True)
    email = graphene.String(
        description='The customer\'s email address.')
    shipping_address = AddressInput(
        description=(
            'The mailing address to where the checkout will be shipped.'))
    billing_address = AddressInput(
        description='Billing address of the customer.')


class CheckoutCreate(ModelMutation, I18nMixin):
    class Arguments:
        input = CheckoutCreateInput(
            required=True, description='Fields required to create checkout.')

    class Meta:
        description = 'Create a new checkout.'
        model = models.Checkout
        return_field_name = 'checkout'

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        user = info.context.user
        lines = data.pop('lines', None)
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = cls.get_nodes_or_error(
                variant_ids, 'variant_id', ProductVariant)
            quantities = [line.get('quantity') for line in lines]

            check_lines_quantity(variants, quantities)

            cleaned_input['variants'] = variants
            cleaned_input['quantities'] = quantities

        default_shipping_address = None
        default_billing_address = None
        if user.is_authenticated:
            default_billing_address = user.default_billing_address
            default_shipping_address = user.default_shipping_address

        if 'shipping_address' in data:
            shipping_address = cls.validate_address(
                data['shipping_address'])
            cleaned_input['shipping_address'] = shipping_address
        else:
            cleaned_input['shipping_address'] = default_shipping_address

        if 'billing_address' in data:
            billing_address = cls.validate_address(
                data['billing_address'])
            cleaned_input['billing_address'] = billing_address
        else:
            cleaned_input['billing_address'] = default_billing_address

        # Use authenticated user's email as default email
        if user.is_authenticated:
            email = data.pop('email', None)
            cleaned_input['email'] = email or user.email

        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        shipping_address = cleaned_input.get('shipping_address')
        billing_address = cleaned_input.get('billing_address')
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()

        instance.save()

        variants = cleaned_input.get('variants')
        quantities = cleaned_input.get('quantities')
        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_checkout(instance, variant, quantity)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user

        # `perform_mutation` is overridden to properly get or create a checkout
        # instance here and abort mutation if needed.
        if user.is_authenticated:
            checkout, created = get_or_create_user_checkout(user)
            # If user has an active checkout, return it without any
            # modifications.
            if not created:
                return CheckoutCreate(checkout=checkout)
        else:
            checkout = models.Checkout()

        cleaned_input = cls.clean_input(info, checkout, data.get('input'))
        checkout = cls.construct_instance(checkout, cleaned_input)
        cls.clean_instance(checkout)
        cls.save(info, checkout, cleaned_input)
        cls._save_m2m(info, checkout, cleaned_input)
        return CheckoutCreate(checkout=checkout)


class CheckoutLinesAdd(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated Checkout.')

    class Arguments:
        checkout_id = graphene.ID(
            description='The ID of the Checkout.', required=True)
        lines = graphene.List(
            CheckoutLineInput,
            required=True,
            description=(
                'A list of checkout lines, each containing information about '
                'an item in the checkout.'))

    class Meta:
        description = 'Adds a checkout line to the existing checkout.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, lines, replace=False):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')

        variant_ids = [line.get('variant_id') for line in lines]
        variants = cls.get_nodes_or_error(
            variant_ids, 'variant_id', ProductVariant)
        quantities = [line.get('quantity') for line in lines]

        check_lines_quantity(variants, quantities)

        # FIXME test if below function is called
        clean_shipping_method(
            checkout=checkout, method=checkout.shipping_method,
            discounts=info.context.discounts,
            taxes=get_taxes_for_address(checkout.shipping_address))

        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_checkout(
                    checkout, variant, quantity, replace=replace)

        recalculate_checkout_discount(
            checkout, info.context.discounts, info.context.taxes)

        return CheckoutLinesAdd(checkout=checkout)


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description='An updated Checkout.')

    class Meta:
        description = 'Updates CheckoutLine in the existing Checkout.'

    @classmethod
    def perform_mutation(cls, root, info, checkout_id, lines):
        return super().perform_mutation(root, info, checkout_id, lines, replace=True)


class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout.')

    class Arguments:
        checkout_id = graphene.ID(
            description='The ID of the Checkout.', required=True)
        line_id = graphene.ID(
            description='ID of the CheckoutLine to delete.')

    class Meta:
        description = 'Deletes a CheckoutLine.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, line_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')
        line = cls.get_node_or_error(
            info, line_id, only_type=CheckoutLine, field='line_id')

        if line and line in checkout.lines.all():
            line.delete()

        # FIXME test if below function is called
        clean_shipping_method(
            checkout=checkout, method=checkout.shipping_method,
            discounts=info.context.discounts,
            taxes=get_taxes_for_address(checkout.shipping_address))

        recalculate_checkout_discount(
            checkout, info.context.discounts, info.context.taxes)

        return CheckoutLineDelete(checkout=checkout)


class CheckoutCustomerAttach(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout.')

    class Arguments:
        checkout_id = graphene.ID(
            required=True, description='ID of the Checkout.')
        customer_id = graphene.ID(
            required=True, description='The ID of the customer.')

    class Meta:
        description = 'Sets the customer as the owner of the Checkout.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, customer_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')
        customer = cls.get_node_or_error(
            info, customer_id, only_type=User, field='customer_id')
        checkout.user = customer
        checkout.save(update_fields=['user'])
        return CheckoutCustomerAttach(checkout=checkout)


class CheckoutCustomerDetach(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)

    class Meta:
        description = 'Removes the user assigned as the owner of the checkout.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')
        checkout.user = None
        checkout.save(update_fields=['user'])
        return CheckoutCustomerDetach(checkout=checkout)


class CheckoutShippingAddressUpdate(BaseMutation, I18nMixin):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='ID of the Checkout.')
        shipping_address = AddressInput(
            required=True,
            description=(
                'The mailing address to where the checkout will be shipped.'))

    class Meta:
        description = 'Update shipping address in the existing Checkout.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, shipping_address):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')
        shipping_address = cls.validate_address(
            shipping_address, instance=checkout.shipping_address)

        # FIXME test if below function is called
        clean_shipping_method(
            checkout=checkout, method=checkout.shipping_method,
            discounts=info.context.discounts,
            taxes=get_taxes_for_address(shipping_address))

        with transaction.atomic():
            shipping_address.save()
            change_shipping_address_in_checkout(checkout, shipping_address)
        recalculate_checkout_discount(
            checkout, info.context.discounts, info.context.taxes)

        return CheckoutShippingAddressUpdate(checkout=checkout)


class CheckoutBillingAddressUpdate(CheckoutShippingAddressUpdate):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='ID of the Checkout.')
        billing_address = AddressInput(
            required=True,
            description=('The billing address of the checkout.'))

    class Meta:
        description = 'Update billing address in the existing Checkout.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, billing_address):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')

        billing_address = cls.validate_address(
            billing_address, instance=checkout.billing_address)
        with transaction.atomic():
            billing_address.save()
            change_billing_address_in_checkout(checkout, billing_address)
        return CheckoutShippingAddressUpdate(checkout=checkout)


class CheckoutEmailUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID')
        email = graphene.String(required=True, description='email')

    class Meta:
        description = 'Updates email address in the existing Checkout object.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, email):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')

        checkout.email = email
        cls.clean_instance(checkout)
        checkout.save(update_fields=['email'])
        return CheckoutEmailUpdate(checkout=checkout)


class CheckoutShippingMethodUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID')
        shipping_method_id = graphene.ID(
            required=True, description='Shipping method')

    class Meta:
        description = 'Updates the shipping address of the checkout.'

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, shipping_method_id):
        checkout_id = from_global_id_strict_type(
            info, checkout_id, only_type=Checkout, field='checkout_id')
        checkout = models.Checkout.objects.prefetch_related(
            'lines__variant__product__collections').get(pk=checkout_id)
        shipping_method = cls.get_node_or_error(
            info, shipping_method_id, only_type=ShippingMethod,
            field='shipping_method_id')

        clean_shipping_method(
            checkout=checkout, method=shipping_method,
            discounts=info.context.discounts, taxes=info.context.taxes,
            remove=False)

        checkout.shipping_method = shipping_method
        checkout.save(update_fields=['shipping_method'])
        recalculate_checkout_discount(
            checkout, info.context.discounts, info.context.taxes)

        return CheckoutShippingMethodUpdate(checkout=checkout)


class CheckoutComplete(BaseMutation):
    order = graphene.Field(Order, description='Placed order')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)

    class Meta:
        description = (
            'Completes the checkout. As a result a new order is created and '
            'a payment charge is made. This action requires a successful '
            'payment before it can be performed.')

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')

        taxes = get_taxes_for_checkout(checkout, info.context.taxes)
        clean_checkout(checkout, taxes, info.context.discounts)

        try:
            order = create_order(
                checkout=checkout,
                tracking_code=analytics.get_client_id(info.context),
                discounts=info.context.discounts, taxes=taxes)
        except InsufficientStock:
            raise ValidationError('Insufficient product stock.')
        except voucher_model.NotApplicable:
            raise ValidationError('Voucher not applicable')

        payment = checkout.get_last_active_payment()

        # remove checkout after checkout is created
        checkout.delete()
        order.events.create(type=OrderEvents.PLACED.value)
        send_order_confirmation.delay(order.pk)
        order.events.create(
            type=OrderEvents.EMAIL_SENT.value,
            parameters={
                'email': order.get_user_current_email(),
                'email_type': OrderEventsEmails.ORDER.value})

        try:
            gateway_process_payment(
                payment=payment, payment_token=payment.token)
        except PaymentError as e:
            raise ValidationError(str(e))
        return CheckoutComplete(order=order)


class CheckoutUpdateVoucher(BaseMutation):
    checkout = graphene.Field(
        Checkout, description='An checkout with updated voucher')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)
        voucher_code = graphene.String(description='Voucher code')

    class Meta:
        description = (
            'Adds voucher to the checkout. Query it without voucher_code '
            'field to remove voucher from checkout.')

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, voucher_code=None):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field='checkout_id')

        if voucher_code:
            try:
                voucher = voucher_model.Voucher.objects.active(
                    date=date.today()).get(code=voucher_code)
            except voucher_model.Voucher.DoesNotExist:
                raise ValidationError({
                    'voucher_code': 'Voucher with given code does not exist.'})

            try:
                add_voucher_to_checkout(voucher, checkout)
            except voucher_model.NotApplicable:
                raise ValidationError({
                    'voucher_code':
                    'Voucher is not applicable to that checkout.'})
        else:
            existing_voucher = get_voucher_for_checkout(checkout)
            if existing_voucher:
                remove_voucher_from_checkout(checkout)

        return CheckoutUpdateVoucher(checkout=checkout)
