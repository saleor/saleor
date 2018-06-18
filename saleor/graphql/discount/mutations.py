import graphene

from ...discount import models
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types import Decimal


class VoucherInput(graphene.InputObjectType):
    type = graphene.String(
        description='Voucher type: product, category shipping or value.')
    name = graphene.String(description='Voucher name.')
    code = graphene.String(decription='Code to use the voucher.')
    start_date = graphene.types.datetime.DateTime(
        description='Start date of the voucher in ISO 8601 format.')
    end_date = graphene.types.datetime.DateTime(
        description='End date of the voucher in ISO 8601 format.')
    discount_value_type = graphene.String(
        description='Choices: fixed or percentage.')
    discount_value = Decimal(description='Value of the voucher.')
    product = graphene.ID(description='Product related to the discount.')
    category = graphene.ID(description='Category related to the discount.')
    apply_to = graphene.String(
        description='Single item (one) or all matching products (all).')
    limit = Decimal(description='Limit value of the discount.')


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
        return user.has_perm('discount.edit_voucher')


class VoucherUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a voucher to update.')
        input = VoucherInput(
            required=True,
            description='Fields required to update a voucher.')

    class Meta:
        description = 'Updates a voucher.'
        model = models.Voucher

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.edit_voucher')


class VoucherDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a voucher to delete.')

    class Meta:
        description = 'Deletes a voucher.'
        model = models.Voucher

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.edit_voucher')


class SaleInput(graphene.InputObjectType):
    name = graphene.String(description='Voucher name.')
    type = graphene.String(description='Fixed or percentage.')
    discount_value = graphene.String(description='Value of the voucher.')
    products = graphene.List(
        graphene.ID, description='Products related to the discount.')
    categories = graphene.List(
        graphene.ID, description='Categories related to the discount.')


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
        return user.has_perm('discount.edit_sale')


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
        return user.has_perm('discount.edit_sale')


class SaleDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a sale to delete.')

    class Meta:
        description = 'Deletes a sale.'
        model = models.Sale

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('discount.edit_sale')
