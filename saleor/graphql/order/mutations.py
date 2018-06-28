import graphene
from graphene.types import InputObjectType
from graphql_jwt.decorators import permission_required

from ...core.utils.taxes import ZERO_TAXED_MONEY
from ...order import OrderStatus, models
from ...shipping.models import ANY_COUNTRY
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import Decimal, Error
from ..utils import get_node
from .types import Order


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
    email = graphene.String(description='Email address.')


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
    email = graphene.String(description='Email address of the customer.')
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


class DraftOrderCreate(ModelMutation):
    class Arguments:
        input = DraftOrderInput(
            required=True,
            description='Fields required to create an order.')

    class Meta:
        description = 'Creates a new variant for a product'
        model = models.Order

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input['status'] = OrderStatus.DRAFT
        display_gross_prices = info.context.site.settings.display_gross_prices
        cleaned_input['display_gross_prices'] = display_gross_prices

        # Set up default addresses if possible
        user = cleaned_input.get('user')
        shipping_address = cleaned_input.get('shipping_address')
        billing_address = cleaned_input.get('billing_address')
        if user and not shipping_address:
            cleaned_input[
                'shipping_address'] = user.default_shipping_address
        if user and not billing_address:
            cleaned_input[
                'billing_address'] = user.default_billing_address
        return cleaned_input

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        instance = super().construct_instance(instance, cleaned_data)
        instance.shipping_address = cleaned_data.get('shipping_address')
        instance.billing_address = cleaned_data.get('billing_address')
        return instance


    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.edit_order')


class DraftOrderUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an order to update.')
        input = DraftOrderInput(
            required=True,
            description='Fields required to update an order.')

    class Meta:
        description = 'Updates an order.'
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
        return user.has_perm('product.edit_product')


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

        return DraftOrderComplete(order=order)
