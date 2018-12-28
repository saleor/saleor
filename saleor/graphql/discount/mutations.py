import graphene

from ...discount import VoucherType, models
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.scalars import Decimal
from .types import DiscountValueTypeEnum, VoucherTypeEnum


def validate_voucher(voucher_data):
    voucher_type = voucher_data.get('type')
    errors = []
    if voucher_type == VoucherType.PRODUCT:
        if not voucher_data.get('products'):
            errors.append(('products', 'This field is required.'))
    elif voucher_type == VoucherType.COLLECTION:
        if not voucher_data.get('collections'):
            errors.append(('collections', 'This field is required.'))
    elif voucher_type == VoucherType.CATEGORY:
        if not voucher_data.get('categories'):
            errors.append(('categories', 'This field is required.'))
    return errors


class VoucherInput(graphene.InputObjectType):
    type = VoucherTypeEnum(
        description='Voucher type: product, category shipping or value.')
    name = graphene.String(description='Voucher name.')
    code = graphene.String(decription='Code to use the voucher.')
    start_date = graphene.types.datetime.DateTime(
        description='Start date of the voucher in ISO 8601 format.')
    end_date = graphene.types.datetime.DateTime(
        description='End date of the voucher in ISO 8601 format.')
    discount_value_type = DiscountValueTypeEnum(
        description='Choices: fixed or percentage.')
    discount_value = Decimal(description='Value of the voucher.')
    products = graphene.List(
        graphene.ID, description='Products discounted by the voucher.',
        name='products')
    collections = graphene.List(
        graphene.ID, description='Collections discounted by the voucher.',
        name='collections')
    categories = graphene.List(
        graphene.ID, description='Categories discounted by the voucher.',
        name='categories')
    min_amount_spent = Decimal(
        description='Min purchase amount required to apply the voucher.')
    countries = graphene.List(
        graphene.String,
        description='Country codes that can be used with the shipping voucher')


class VoucherCreate(ModelMutation):
    class Arguments:
        input = VoucherInput(
            required=True,
            description='Fields required to create a voucher.')

    class Meta:
        description = 'Creates a new voucher.'
        model = models.Voucher

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.manage_discounts')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        voucher_errors = validate_voucher(cleaned_input)
        for err in voucher_errors:
            cls.add_error(errors=errors, field=err[0], message=err[1])
        return cleaned_input


class VoucherUpdate(VoucherCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a voucher to update.')
        input = VoucherInput(
            required=True,
            description='Fields required to update a voucher.')

    class Meta:
        description = 'Updates a voucher.'
        model = models.Voucher


class VoucherDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a voucher to delete.')

    class Meta:
        description = 'Deletes a voucher.'
        model = models.Voucher

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.manage_discounts')


class SaleInput(graphene.InputObjectType):
    name = graphene.String(description='Voucher name.')
    type = DiscountValueTypeEnum(description='Fixed or percentage.')
    value = Decimal(description='Value of the voucher.')
    products = graphene.List(
        graphene.ID, description='Products related to the discount.',
        name='products')
    categories = graphene.List(
        graphene.ID, description='Categories related to the discount.',
        name='categories')
    collections = graphene.List(
        graphene.ID, description='Collections related to the discount.',
        name='collections')
    start_date = graphene.types.datetime.DateTime(
        description='Start date of the sale in ISO 8601 format.')
    end_date = graphene.types.datetime.DateTime(
        description='End date of the sale in ISO 8601 format.')


class SaleCreate(ModelMutation):
    class Arguments:
        input = SaleInput(
            required=True,
            description='Fields required to create a sale.')

    class Meta:
        description = 'Creates a new sale.'
        model = models.Sale

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.manage_discounts')


class SaleUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a sale to update.')
        input = SaleInput(
            required=True,
            description='Fields required to update a sale.')

    class Meta:
        description = 'Updates a sale.'
        model = models.Sale

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.manage_discounts')


class SaleDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a sale to delete.')

    class Meta:
        description = 'Deletes a sale.'
        model = models.Sale

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.manage_discounts')
