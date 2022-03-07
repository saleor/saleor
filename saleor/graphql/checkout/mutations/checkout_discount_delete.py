import graphene

from ....permission.enums import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError
from ..types import Checkout


class CheckoutDiscountDelete(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="Checkout which has removed discount."
    )

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to remove.", required=True
        )

    class Meta:
        description = "Delete discount from the checkout."
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutError
