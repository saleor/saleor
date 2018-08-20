import graphene
from django.db import transaction

from ...account.models import Address
from ...checkout import models
from ...checkout.utils import add_variant_to_cart
from ..account.types import AddressInput, User
from ..core.mutations import BaseMutation, ModelMutation
from ..order.mutations.draft_orders import check_lines_quantity
from ..product.types import ProductVariant
from ..utils import get_node, get_nodes
from .types import Checkout, CheckoutLine


class CheckoutLineInput(graphene.InputObjectType):
    quantity = graphene.Int(description='quantity')
    variant_id = graphene.ID(description='ID of product variant')


class CheckoutCreateInput(graphene.InputObjectType):
    lines = graphene.List(
        CheckoutLineInput, description='Checkout lines')
    email = graphene.String(description='Customer email')
    shipping_address = AddressInput(description='Shipping address')


class CheckoutCreate(ModelMutation):
    class Arguments:
        input = CheckoutCreateInput(
            required=True, description='Data required to create Checkout')

    class Meta:
        description = 'Create a new Checkout'
        model = models.Cart
        return_field_name = 'checkout'

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        shipping_address = input.pop('shipping_address', None)
        cleaned_input = super().clean_input(info, instance, input, errors)
        lines = input.pop('lines', None)
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = get_nodes(variant_ids, ProductVariant)
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
    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)
        lines = graphene.List(
            CheckoutLineInput, description='Checkout lines', required=True)

    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Meta:
        description = 'Adds a checkout line to existing checkout'

    @classmethod
    def mutate(cls, root, info, checkout_id, lines, replace=False):
        checkout = get_node(info, checkout_id, only_type=Checkout)
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
                add_variant_to_cart(checkout, variant, quantity, replace=replace)
        return CheckoutLinesAdd(checkout=checkout, errors=errors)


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Meta:
        description = 'Updates checkout line in existing checkout'

    @classmethod
    def mutate(cls, root, info, checkout_id, lines):
        return super().mutate(root, info, checkout_id, lines, replace=True)


class CheckoutLineDelete(BaseMutation):
    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)
        line_id = graphene.ID(description='Checkout line ID')

    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Meta:
        description = 'Deletes a checkout line'

    @classmethod
    def mutate(cls, root, info, checkout_id, line_id):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        line = cls.get_node_or_error(
            info, line_id, errors, 'line_id', only_type=CheckoutLine)
        line.delete()
        return CheckoutLinesAdd(checkout=checkout, errors=errors)



class CheckoutCustomerAttach(BaseMutation):
    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)
        customer_id = graphene.ID(description='Customer ID', required=True)

    checkout = graphene.Field(Checkout, description='An updated checkout')

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
    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID', required=True)


    checkout = graphene.Field(Checkout, description='An updated checkout')

    @classmethod
    def mutate(cls, root, info, checkout_id):
        checkout = get_node(info, checkout_id, only_type=Checkout)
        if checkout:
            checkout.user = None
            checkout.save(update_fields=['user'])
        return CheckoutCustomerDetach(checkout=checkout)

class CheckoutShippingAddressUpdate(BaseMutation):
    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID')
        shipping_address = AddressInput(description='Shipping address')

    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Meta:
        description = 'Update shipping address in existing Checkout object'

    @classmethod
    def mutate(cls, root, info, checkout_id, shipping_address):
        errors = {}
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        shipping_address = Address(**shipping_address)
        if checkout and shipping_address:
            with transaction.atomic():
                shipping_address.save()
                checkout.shipping_address = shipping_address
                checkout.save(update_fields=['shipping_address'])
        return CheckoutShippingAddressUpdate(checkout=checkout, errors=errors)

class CheckoutEmailUpdate(BaseMutation):
    class Arguments:
        checkout_id = graphene.ID(description='Checkout ID')
        email = graphene.String(required=True, description='email')

    checkout = graphene.Field(Checkout, description='An updated checkout')

    class Meta:
        description = 'Update email address in existing Checkout object'

    @classmethod
    def mutate(cls, root, info, checkout_id, email):
        errors = []
        checkout = cls.get_node_or_error(
            info, checkout_id, errors, 'checkout_id', only_type=Checkout)
        if checkout:
            checkout.email = email
            checkout.save(update_fields=['email'])

        return CheckoutEmailUpdate(checkout=checkout, errors=errors)
