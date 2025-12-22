from typing import cast

import graphene

from .....account import models
from .....account.search import prepare_user_search_document_value
from .....core.tracing import traced_atomic_transaction
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....account.mixins import AddressMetadataMixin
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_319
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....meta.inputs import MetadataInput, MetadataInputDescription
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise
from ...mixins import AppImpersonateMixin
from ...types import AddressInput, User
from ..base import BaseCustomerCreate
from .base import AccountBaseInput
from .utils import ACCOUNT_UPDATE_FIELDS


class AccountInput(AccountBaseInput):
    default_billing_address = AddressInput(
        description="Billing address of the customer."
    )
    default_shipping_address = AddressInput(
        description="Shipping address of the customer."
    )
    metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the user metadata. "
            f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}"
        ),
        required=False,
    )

    class Meta:
        description = "Fields required to update the user."
        doc_category = DOC_CATEGORY_USERS


class AccountUpdate(AddressMetadataMixin, BaseCustomerCreate, AppImpersonateMixin):
    class Arguments:
        input = AccountInput(
            description="Fields required to update the account of the logged-in user.",
            required=True,
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
            "Updates the account of the logged-in user.\n\n"
            "Requires one of following set of permissions: "
            "AUTHENTICATED_USER or AUTHENTICATED_APP + IMPERSONATE_USER."
        )
        doc_category = DOC_CATEGORY_USERS
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (
            AuthorizationFilters.AUTHENTICATED_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = AccountError
        error_type_field = "account_errors"
        support_meta_field = True
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_UPDATED,
                description="A customer account was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED,
                description="Optionally called when customer's metadata was updated.",
            ),
        ]
        instance_tracker_fields = list(ACCOUNT_UPDATE_FIELDS)

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        customer_id = data.get("customer_id")
        user = cls.get_user_instance(info, customer_id)
        user = cast(models.User, user)
        data["id"] = graphene.Node.to_global_id("User", user.id)
        return super().perform_mutation(root, info, **data)

    @classmethod
    @traced_atomic_transaction()
    def save(
        cls,
        info: ResolveInfo,
        instance: models.User,
        cleaned_input,
        instance_tracker=None,
    ):
        modified_instance_fields = set(instance_tracker.get_modified_fields())
        site = get_site_promise(info.context).get()
        use_legacy_webhooks_emission = site.settings.use_legacy_update_webhook_emission
        meta_modified_fields = {"metadata"} & modified_instance_fields
        manager = get_plugin_manager_promise(info.context).get()

        if changed_fields := cls.save_default_addresses(
            cleaned_input=cleaned_input, user_instance=instance
        ):
            modified_instance_fields.update(changed_fields)

        non_metadata_modified_fields = modified_instance_fields - meta_modified_fields
        if non_metadata_modified_fields:
            instance.search_document = prepare_user_search_document_value(instance)
            modified_instance_fields.add("search_document")

        if modified_instance_fields:
            modified_instance_fields.add("updated_at")
            instance.save(update_fields=list(modified_instance_fields))

        if non_metadata_modified_fields or (
            use_legacy_webhooks_emission and meta_modified_fields
        ):
            cls.call_event(manager.customer_updated, instance)

        if meta_modified_fields:
            cls.call_event(manager.customer_metadata_updated, instance)
