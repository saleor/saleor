import graphene

from .....account import models
from .....account.search import prepare_user_search_document_value
from .....account.utils import (
    remove_the_oldest_user_address_if_address_limit_is_reached,
)
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.mixins import AddressMetadataMixin
from ....account.types import Address, AddressInput, User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import DeprecatedModelMutation
from ....core.types import AccountError
from ....directives import doc, webhook_events
from ....plugins.dataloaders import get_plugin_manager_promise
from ...i18n import I18nMixin


@doc(category=DOC_CATEGORY_USERS)
@webhook_events({WebhookEventAsyncType.ADDRESS_CREATED})
class AddressCreate(AddressMetadataMixin, DeprecatedModelMutation, I18nMixin):
    """Creates a user address."""

    user = graphene.Field(
        User, description="A user instance for which the address was created."
    )

    class Arguments:
        user_id = graphene.ID(
            description="ID of a user to create address for.", required=True
        )
        input = AddressInput(
            description="Fields required to create address.", required=True
        )

    class Meta:
        model = models.Address
        object_type = Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        user_id = data["user_id"]
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        with traced_atomic_transaction():
            cleaned_input = cls.clean_input(info, instance, data)
            instance = cls.validate_address(cleaned_input, instance=instance, info=info)
            cls.clean_instance(info, instance)
            cls.save(info, instance, cleaned_input)
            cls.post_save_action(info, instance, cleaned_input)
            response = cls.success_response(instance)
            response.user = user
            remove_the_oldest_user_address_if_address_limit_is_reached(user)
            user.addresses.add(instance)
            user.search_document = prepare_user_search_document_value(user)

            user.save(update_fields=["search_document", "updated_at"])
        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.address_created, instance)
