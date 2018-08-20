import graphene
from ..core.mutations import ModelMutation, ModelDeleteMutation, BaseMutation
from ...checkout import models
from ..account.types import AddressInput
from ...account.models import Address
from ..product.types import ProductVariant
from ..order.mutations.draft_orders import check_lines_quantity
from ...checkout.utils import add_variant_to_cart
from .types import Checkout

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
            variants = cls.get_nodes_or_error(
                ids=variant_ids, only_type=ProductVariant, errors=errors,
                field='variants')
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
        instance.save(update_fields=['billing_address', 'shipping_address'])
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
    def mutate(cls, root, info, checkout_id, lines):
        errors = []
        checkout = cls.get_node_or_error(
            id=checkout_id, only_type=Checkout, errors=errors,
            field='checkout_id', info=info)
        if errors:
            return cls(errors=errors)
        cleaned_data = {}
        if lines:
            variant_ids = [line.get('variant_id') for line in lines]
            variants = cls.get_nodes_or_error(
                ids=variant_ids, only_type=ProductVariant, errors=errors,
                field='variants')
            quantities = [line.get('quantity') for line in lines]
            line_errors = check_lines_quantity(variants, quantities)
            if line_errors:
                for err in line_errors:
                    cls.add_error(errors, field=err[0], message=err[1])
            else:
                cleaned_data['variants'] = variants
                cleaned_data['quantities'] = quantities

        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_cart(checkout, variant, quantity)
        return CheckoutLinesAdd(checkout=checkout)

# class CheckoutLineUpdate(ModelMutation):
#     class Arguments:
#         checkout_id = graphene.ID(description='Checkout ID', required=True)
#         lines = graphene.List(
#             CheckouLineInput, description='Checkout lines', required=True)

#     checkout = Checkout()

#     class Meta:
#         description = 'Adds a checkout line to existing checkout'


# class CheckoutLineDelete(ModelDeleteMutation):
#     class Arguments:
#         id = graphene.ID(description='Checkout line ID')

#     class Meta:
#         description = 'Deletes a checkout line'
#         model = models.CartLine


# class CheckoutCustomerAttach(ModelMutation):
#     class Arguments:
#         checkout = graphene.ID(description='Checkout ID')
#         customer_id = graphene.ID(description='Customer ID')

# class CheckoutCustomerDetach(ModelMutation):
#     class Arguments:
#         checkout = graphene.ID(description='Checkout ID')

# class CheckoutShippingAddressUpdate(ModelMutation):
#     class Arguments:
#         checkout = graphene.ID(description='Checkout ID')
#         shipping_address = AddressInput(description='Shipping address')


# class CheckoutEmailUpdate(ModelMutation):
#     class Arguments:
#         checkout = graphene.ID(description='Checkout ID')
#         email = graphene.String(required=True, description='email')
