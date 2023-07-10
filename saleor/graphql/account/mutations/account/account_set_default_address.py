from typing import cast

import graphene
from django.core.exceptions import ValidationError

from .....account import models, utils
from .....account.error_codes import AccountErrorCode
from .....checkout import AddressType
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import AddressTypeEnum
from ...types import Address, User


class AccountSetDefaultAddress(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the address to set as default."
        )
        type = AddressTypeEnum(required=True, description="The type of address.")

    class Meta:
        description = "Sets a default address for the authenticated user."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_UPDATED,
                description="A customer's address was updated.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, type
    ):
        address = cls.get_node_or_error(info, id, only_type=Address)
        user = info.context.user
        user = cast(models.User, user)

        if not user.addresses.filter(pk=address.pk).exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The address doesn't belong to that user.",
                        code=AccountErrorCode.INVALID.value,
                    )
                }
            )

        if type == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING
        manager = get_plugin_manager_promise(info.context).get()
        utils.change_user_default_address(user, address, address_type, manager)
        cls.call_event(manager.customer_updated, user)
        return cls(user=user)
