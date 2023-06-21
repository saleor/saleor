import graphene

from ....account import models as account_models
from ....permission.enums import SitePermissions
from ...account.types import StaffNotificationRecipient
from ...core.types import ShopError
from .staff_notification_recipient_create import (
    StaffNotificationRecipientCreate,
    StaffNotificationRecipientInput,
)


class StaffNotificationRecipientUpdate(StaffNotificationRecipientCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a staff notification recipient to update."
        )
        input = StaffNotificationRecipientInput(
            required=True,
            description="Fields required to update a staff notification recipient.",
        )

    class Meta:
        description = "Updates a staff notification recipient."
        model = account_models.StaffNotificationRecipient
        object_type = StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"
