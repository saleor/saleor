import graphene

from ...core.permissions import GiftcardPermissions
from ...giftcard import models
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types.common import GiftCardError


class GiftCardBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of gift card IDs to delete."
        )

    class Meta:
        description = "Delete gift cards."
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
