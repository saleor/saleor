import graphene

from ....account import models as account_models
from ....permission.enums import SitePermissions
from ...account.types import StaffNotificationRecipient
from ...core.mutations import ModelDeleteMutation
from ...core.types import ShopError


class StaffNotificationRecipientDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a staff notification recipient to delete."
        )

    class Meta:
        description = "Delete staff notification recipient."
        model = account_models.StaffNotificationRecipient
        object_type = StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"
