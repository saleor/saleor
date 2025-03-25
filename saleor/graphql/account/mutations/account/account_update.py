from typing import cast
from urllib.parse import urlencode

import graphene
from django.contrib.auth.tokens import default_token_generator

from .....account import events as account_events
from .....account import models
from .....account.error_codes import AccountErrorCode
from .....account.notifications import send_set_password_notification
from .....account.search import prepare_user_search_document_value
from .....core.tracing import traced_atomic_transaction
from .....core.utils.url import prepare_url
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....account.mixins import AddressMetadataMixin
from ....channel.utils import clean_channel, validate_channel
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_319
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...mixins import AppImpersonateMixin
from ...types import AddressInput, User
from ..base import BILLING_ADDRESS_FIELD, SHIPPING_ADDRESS_FIELD, BaseCustomerCreate
from .base import AccountBaseInput


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

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        customer_id = data.get("customer_id")
        user = cls.get_user_instance(info, customer_id)
        user = cast(models.User, user)
        data["id"] = graphene.Node.to_global_id("User", user.id)
        return super().perform_mutation(root, info, **data)

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        default_shipping_address = cleaned_input.get(SHIPPING_ADDRESS_FIELD)
        manager = get_plugin_manager_promise(info.context).get()
        if default_shipping_address:
            default_shipping_address.save()
            instance.default_shipping_address = default_shipping_address
        default_billing_address = cleaned_input.get(BILLING_ADDRESS_FIELD)
        if default_billing_address:
            default_billing_address.save()
            instance.default_billing_address = default_billing_address

        is_creation = instance.pk is None
        super().save(info, instance, cleaned_input)
        if default_billing_address:
            instance.addresses.add(default_billing_address)
        if default_shipping_address:
            instance.addresses.add(default_shipping_address)

        instance.search_document = prepare_user_search_document_value(instance)
        instance.save(update_fields=["search_document", "updated_at"])

        # The instance is a new object in db, create an event
        if is_creation:
            cls.call_event(manager.customer_created, instance)
            account_events.customer_account_created_event(user=instance)
        else:
            cls.call_event(manager.customer_updated, instance)

        if redirect_url := cleaned_input.get("redirect_url"):
            channel_slug = cleaned_input.get("channel")
            if not instance.is_staff:
                channel_slug = clean_channel(
                    channel_slug, error_class=AccountErrorCode, allow_replica=False
                ).slug
            elif channel_slug is not None:
                channel_slug = validate_channel(
                    channel_slug, error_class=AccountErrorCode
                ).slug
            send_set_password_notification(
                redirect_url,
                instance,
                manager,
                channel_slug,
            )
            token = default_token_generator.make_token(instance)
            params = urlencode({"email": instance.email, "token": token})
            cls.call_event(
                manager.account_set_password_requested,
                instance,
                channel_slug,
                token,
                prepare_url(params, redirect_url),
            )
