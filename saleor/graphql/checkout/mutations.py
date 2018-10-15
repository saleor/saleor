import graphene
from django.db import transaction

from ...account.models import Address
from ...checkout import models
from ...checkout.utils import (
    add_variant_to_cart, change_billing_address_in_cart,
    change_shipping_address_in_cart, create_order, get_taxes_for_cart,
    ready_to_place_order)
from ...core import analytics
from ...core.exceptions import InsufficientStock
from ...core.utils.taxes import get_taxes_for_address
from ...shipping.models import ShippingMethod as ShippingMethodModel
from ..account.types import AddressInput, User
from ..core.mutations import BaseMutation, ModelMutation
from ..core.types.common import Error
from ..order.types import Order
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from .types import Checkout, CheckoutLine


def clean_shipping_method(
        checkout, method, errors, discounts, taxes, country_code=None):
    # FIXME Add tests for this function
    if not method:
        return errors
    if not checkout.is_shipping_required():
        errors.append(
            Error(
                field='checkout',
                message='This checkout does not requires shipping.'))
    if not checkout.shipping_address:
        errors.append(
            Error(
                field='checkout',
                message=(
                    'Cannot choose a shipping method for a '
                    'checkout without the shipping address.')))
        return errors
    valid_methods = (
        ShippingMethodModel.objects.applicable_shipping_methods(
            price=checkout.get_subtotal(discounts, taxes).gross.amount,
            weight=checkout.get_total_weight(),
            country_code=country_code or checkout.shipping_address.country.code
        ))
    valid_methods = valid_methods.values_list('id', flat=True)
    if method.pk not in valid_methods:
        errors.append(
            Error(
                field='shippingMethod',
                message='Shipping method cannot be used with this checkout.'))
    return errors


def check_lines_quantity(variants, quantities):
    """Check if stock is sufficient for each line in the list of dicts.
    Return list of errors.
    """
    # FIXME Add tests
    errors = []

    for variant, quantity in zip(variants, quantities):
        try:
            variant.check_quantity(quantity)
        except InsufficientStock as e:
            message = (
                'Add line mutation error',
                'Could not add item. Only %(remaining)d remaining in stock.' %
                {'remaining': e.item.quantity_available})
            errors.append((variant.name, message))
    return errors


class CheckoutLineInput(graphene.InputObjectType):
    quantity = graphene.Int(
        description='The number of items purchased.')
    variant_id = graphene.ID(description='ID of the ProductVariant.')


class CheckoutCreateInput(graphene.InputObjectType):
    lines = graphene.List(
        CheckoutLineInput,
        description=(
            'A list of checkout lines, each containing information about '
            'an item in the checkout.'))
    email = graphene.String(description='The customer\'s email address.')
    shipping_address = AddressInput(
        description=(
            'The mailling address to where the checkout will be shipped.'))


class CheckoutCreate(ModelMutation):
    class Arguments:
        input = CheckoutCreateInput(
            required=True, description='Fields required to create a Checkout.')

    class Meta:
        description = 'Create a new Checkout.'
        model = models.Cart
        return_field_name = 'checkout'

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        shipping_address = input.pop('shipping_address', None)
        cleaned_input = super().clean_input(info, instance, input, errors)
        lines = input.pop('lines', None)
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = cls.get_nodes_or_error(
                ids=variant_ids, errors=errors, field='variant_id',
                only_type=ProductVariant)
            quantities = [line.get('quantity') for line in lines]
            line_errors = check_lines_quantity(variants, quantities)
            if line_errors:
                for err in line_errors:
                    cls.add_error(errors, field=err[0], message=err[1])
            else:
                cleaned_input['variants'] = variants
                cleaned_input['quantities'] = quantities

        if shipping_address:
            shipping_address = Address(**shipping_address)
            cls.clean_instance(shipping_address, errors)
            cleaned_input['shipping_address'] = shipping_address
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        shipping_address = cleaned_input.get('shipping_address')
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address
        super().save(info, instance, cleaned_input)
        instance.save(update_fields=['shipping_address'])
        variants = cleaned_input.get('variants')
        quantities = cleaned_input.get('quantities')
        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_cart(instance, variant, quantity)


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
        description = 'Adds a checkout line to existing checkout.'

    @classmethod
    def mutate(cls, root, info, checkout_id, lines, replace=False):
        checkout = graphene.Node.get_node_from_global_id(
            info, checkout_id, Checkout)
        variants, quantities = None, None
        errors = []
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = cls.get_nodes_or_error(
                ids=variant_ids, errors=errors, field='variant_id',
                only_type=ProductVariant)
            quantities = [line.get('quantity') for line in lines]
            line_errors = check_lines_quantity(variants, quantities)
            if line_errors:
                for err in line_errors:
                    cls.add_error(errors, field=err[0], message=err[1])

        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_cart(
                    checkout, variant, quantity, replace=replace)
        return CheckoutLinesAdd(checkout=checkout, errors=errors)


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description='An updated Checkout.')

    class Meta:
        description = 'Updates CheckoutLine in the existing Checkout.'

    @classmethod
    def mutate(cls, root, info, checkout_id, lines):
        return super().mutate(root, info, checkout_id, lines, replace=True)


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
    def mutate(cls, root, info, checkout_id, line_id):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        line = cls.get_node_or_error(
            info, line_id, errors, 'line_id', only_type=CheckoutLine)
        if line and line in checkout.lines.all():
            line.delete()
        return CheckoutLinesAdd(checkout=checkout, errors=errors)


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
    def mutate(cls, root, info, checkout_id, customer_id):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        customer = cls.get_node_or_error(
            info, customer_id, errors, 'customer_id', only_type=User)
        if checkout and customer:
            checkout.user = customer
            checkout.save(update_fields=['user'])
        return CheckoutCustomerAttach(checkout=checkout, errors=errors)


class CheckoutCustomerDetach(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)

    class Meta:
        description = 'Update shipping address in existing Checkout object'

    @classmethod
    def mutate(cls, root, info, checkout_id):
        errors = []
        checkout = graphene.Node.get_node_from_global_id(
            info, checkout_id, Checkout)
        if not checkout.user:
            cls.add_error(
                errors,
                field=None,
                message='There\'s no customer assigned to this Checkout.')
            return CheckoutCustomerDetach(errors=errors)
        if checkout:
            checkout.user = None
            checkout.save(update_fields=['user'])
        return CheckoutCustomerDetach(checkout=checkout)


class CheckoutShippingAddressUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='ID of the Checkout.')
        shipping_address = AddressInput(
            description=(
                'The mailling address to where the checkout will be shipped.'))

    class Meta:
        description = 'Update shipping address in the existing Checkout.'

    @classmethod
    def clean_address(cls, address, errors):
        if address:
            address = Address(**address)
            cls.clean_instance(address, errors)
        return address

    @classmethod
    def mutate(
            cls, root, info, checkout_id, shipping_address):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        if shipping_address:
            shipping_address = cls.clean_address(shipping_address, errors)
        if errors:
            return CheckoutShippingAddressUpdate(errors=errors)

        clean_shipping_method(
            checkout, checkout.shipping_method, errors,
            info.context.discounts, get_taxes_for_address(shipping_address))
        if errors:
            CheckoutShippingAddressUpdate(errors=errors)

        if checkout and shipping_address:
            with transaction.atomic():
                shipping_address.save()
                change_shipping_address_in_cart(checkout, shipping_address)
        return CheckoutShippingAddressUpdate(checkout=checkout, errors=errors)


class CheckoutBillingAddressUpdate(CheckoutShippingAddressUpdate):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='ID of the Checkout.')
        billing_address = AddressInput(
            description=(
                'The billing address of the checkout.'))

    class Meta:
        description = 'Update billing address in the existing Checkout.'

    @classmethod
    def mutate(
            cls, root, info, checkout_id, billing_address):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        if billing_address:
            billing_address = cls.clean_address(billing_address, errors)
        if errors:
            return CheckoutBillingAddressUpdate(errors=errors)

        if checkout and billing_address:
            with transaction.atomic():
                billing_address.save()
                change_billing_address_in_cart(checkout, billing_address)
        return CheckoutShippingAddressUpdate(checkout=checkout, errors=errors)


class CheckoutEmailUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID')
        email = graphene.String(required=True, description='email')

    class Meta:
        description = 'Updates email address in the existing Checkout object.'

    @classmethod
    def mutate(cls, root, info, checkout_id, email):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        if checkout:
            checkout.email = email
            checkout.save(update_fields=['email'])

        return CheckoutEmailUpdate(checkout=checkout, errors=errors)


class CheckoutShippingMethodUpdate(BaseMutation):
    # FIXME test this mutations
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID')
        shipping_method_id = graphene.ID(
            required=True, description='Shipping method')

    @classmethod
    def mutate(cls, root, info, checkout_id, shipping_method_id):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        shipping_method = cls.get_node_or_error(
            info, shipping_method_id, errors, 'shipping_method_id',
            only_type=ShippingMethod)

        clean_shipping_method(
            checkout, shipping_method, errors, info.context.discounts,
            info.context.taxes)
        if errors:
            return CheckoutShippingMethodUpdate(errors=errors)

        checkout.shipping_method = shipping_method
        checkout.save(update_fields=['shipping_method'])
        return CheckoutShippingMethodUpdate(checkout=checkout, errors=errors)


class CheckoutComplete(BaseMutation):
    order = graphene.Field(Order, description='Placed order')

    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID')

    @classmethod
    def mutate(cls, root, info, checkout_id):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        if not checkout:
            return CheckoutComplete(errors=errors)
        ready, checkout_error = ready_to_place_order(checkout)
        if not ready:
            cls.add_error(field=None, message=checkout_error, errors=errors)
            return CheckoutComplete(errors=errors)

        try:
            order = create_order(
                cart=checkout,
                tracking_code=analytics.get_client_id(info.context),
                discounts=info.context.discounts,
                taxes=get_taxes_for_cart(checkout, info.context.taxes))
        except InsufficientStock:
            order = None
            cls.add_error(
                field=None, message='Insufficient product stock.',
                errors=errors)
        return CheckoutComplete(order=order, errors=errors)
