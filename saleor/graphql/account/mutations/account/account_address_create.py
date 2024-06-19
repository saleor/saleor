from typing import cast

import graphene

from .....account import models, search, utils
from .....account.utils import (
    remove_the_oldest_user_address_if_address_limit_is_reached,
)
from .....core.tracing import traced_atomic_transaction
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_319
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import AddressTypeEnum
from ...i18n import I18nMixin
from ...mixins import AddressMetadataMixin, AppImpersonateMixin
from ...types import Address, AddressInput, User


class AccountAddressCreate(
    AddressMetadataMixin, ModelMutation, I18nMixin, AppImpersonateMixin
):
    user = graphene.Field(
        User, description="A user instance for which the address was created."
    )

    class Arguments:
        input = AddressInput(
            description="Fields required to create address.", required=True
        )
        type = AddressTypeEnum(
            required=False,
            description=(
                "A type of address. If provided, the new address will be "
                "automatically assigned as the customer's default address "
                "of that type."
            ),
        )
        customer_id = graphene.ID(
            required=False,
            description=(
                "ID of customer the application is impersonating. "
                "The field can be used and is required by apps only. "
                "Requires IMPERSONATE_USER and AUTHENTICATED_APP permission."
                + ADDED_IN_319
            ),
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Create a new address for the customer.\n\n"
            "Requires one of following set of permissions: "
            "AUTHENTICATED_USER or AUTHENTICATED_APP + IMPERSONATE_USER."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.Address
        object_type = Address
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (
            AuthorizationFilters.AUTHENTICATED_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_UPDATED,
                description="A customer account was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ADDRESS_CREATED,
                description="An address was created.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, type=None, customer_id=None
    ):
        address_type = type
        cleaned_input = cls.clean_input(info=info, instance=Address(), data=input)
        user = cls.get_user_instance(info, customer_id)
        user = cast(models.User, user)
        with traced_atomic_transaction():
            address = cls.validate_address(
                cleaned_input, address_type=address_type, info=info
            )
            cls.clean_instance(info, address)
            cleaned_input["user"] = user
            cls.save(info, address, cleaned_input)
            cls._save_m2m(info, address, cleaned_input)
            if address_type:
                manager = get_plugin_manager_promise(info.context).get()
                utils.change_user_default_address(user, address, address_type, manager)
        return AccountAddressCreate(user=user, address=address)

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        user = cleaned_input.pop("user")
        super().save(info, instance, cleaned_input)
        remove_the_oldest_user_address_if_address_limit_is_reached(user)
        instance.user_addresses.add(user)
        user.search_document = search.prepare_user_search_document_value(user)
        user.save(update_fields=["search_document", "updated_at"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_updated, user)
        cls.call_event(manager.address_created, instance)
