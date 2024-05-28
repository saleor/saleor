from typing import cast

import graphene

from .....account import models
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....account.mixins import AddressMetadataMixin
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_314, ADDED_IN_319
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....meta.inputs import MetadataInput
from ...mixins import AppImpersonateMixin
from ...types import AddressInput, User
from ..base import BaseCustomerCreate
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
        description="Fields required to update the user metadata." + ADDED_IN_314,
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
