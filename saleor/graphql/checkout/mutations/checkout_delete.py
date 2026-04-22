import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.models import Checkout as CheckoutModel
from ....permission.enums import CheckoutPermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_324
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.enums import CheckoutErrorCode as CheckoutErrorCodeEnum
from ...core.mutations import BaseMutation
from ...core.types import Error
from ..types import Checkout


class CheckoutDeleteError(Error):
    code = CheckoutErrorCodeEnum(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutDelete(BaseMutation):
    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_324,
            required=True,
        )

    class Meta:
        description = "Deletes a checkout." + ADDED_IN_324
        doc_category = DOC_CATEGORY_CHECKOUT
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutDeleteError

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        checkout = cls.get_node_or_error(
            info,
            id,
            only_type=Checkout,
            qs=CheckoutModel.objects,
            code=CheckoutErrorCode.NOT_FOUND.value,
        )
        checkout.delete()
        return CheckoutDelete()
