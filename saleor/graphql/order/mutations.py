import graphene
from graphene.types import InputObjectType

from ..core.mutations import BaseMutation
from ..core.types import Decimal


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
    customer_id = graphene.ID(
        descripton='Customer associated with the draft order.')
    email = graphene.String(description='Email address of the customer.')
    discount = Decimal(description='Discount amount for the order.')
    lines = graphene.List(
        LineInput,
        description="""Variant line input consisting of variant ID 
        and quantity of products.""")
    shipping_address = AddressInput(
        description='Address to where the order will be shipped.')
    shipping_method_id = graphene.ID('ID of a selected shipping method.')
    voucher = graphene.ID(
        description='ID of the voucher associated with the order')


class DraftOrderCreate(BaseMutation):
    class Arguments:
        input = DraftOrderInput(required=True)


    @classmethod
    def mutate(cls, root, info, input):
        pass
