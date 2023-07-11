import graphene
from django.core.exceptions import ValidationError

from .....account import utils
from .....account.error_codes import AccountErrorCode
from .....checkout import AddressType
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.enums import AddressTypeEnum
from ....account.types import Address, User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise


class AddressSetDefault(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        address_id = graphene.ID(required=True, description="ID of the address.")
        user_id = graphene.ID(
            required=True, description="ID of the user to change the address for."
        )
        type = AddressTypeEnum(required=True, description="The type of address.")

    class Meta:
        description = "Sets a default address for the given user."
        doc_category = DOC_CATEGORY_USERS
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_UPDATED,
                description="A customer was updated.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, address_id, user_id, type
    ):
        address = cls.get_node_or_error(
            info, address_id, field="address_id", only_type=Address
        )
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)

        if not user.addresses.filter(pk=address.pk).exists():
            raise ValidationError(
                {
                    "address_id": ValidationError(
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
