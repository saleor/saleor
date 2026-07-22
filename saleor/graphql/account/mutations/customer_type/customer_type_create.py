from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.lock_objects import customer_type_qs_select_for_update
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import CustomerTypePermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerTypeCreateErrorCode
from ....core.mutations import DeprecatedModelMutation
from ....core.types import BaseInputObjectType, Error
from ....core.utils import WebhookEventInfo
from ....core.validators import validate_slug_and_generate_if_needed
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import CustomerType


class CustomerTypeCreateError(Error):
    code = CustomerTypeCreateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeCreateInput(BaseInputObjectType):
    name = graphene.String(description="Name of the customer type.")
    slug = graphene.String(
        description=(
            "Slug of the customer type. If not provided, it will be generated "
            "from the name."
        )
    )
    is_default = graphene.Boolean(
        description=(
            "Determines if the customer type should become the default one, "
            "assigned to every newly created user. Passing `true` clears the "
            "flag on the current default customer type - exactly one default "
            "customer type always exists."
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeDefaultTransferMixin:
    """Atomically transfer the default flag when `isDefault: true` is passed.

    The whole mutation runs in a transaction that locks customer type rows and
    clears the current default before the instance is validated and saved, so
    the partial unique constraint on `is_default` is never violated.
    """

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        input_data = data.get("input") or {}
        if not input_data.get("is_default"):
            return super().perform_mutation(root, info, **data)  # type: ignore[misc]
        with traced_atomic_transaction():
            locked_pks = list(
                customer_type_qs_select_for_update().values_list("pk", flat=True)
            )
            models.CustomerType.objects.filter(
                pk__in=locked_pks, is_default=True
            ).update(is_default=False)
            return super().perform_mutation(root, info, **data)  # type: ignore[misc]


class CustomerTypeCreate(CustomerTypeDefaultTransferMixin, DeprecatedModelMutation):
    class Arguments:
        input = CustomerTypeCreateInput(
            description="Fields required to create a customer type.", required=True
        )

    class Meta:
        description = "Creates a new customer type." + ADDED_IN_323
        model = models.CustomerType
        object_type = CustomerType
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)
        error_type_class = CustomerTypeCreateError
        doc_category = DOC_CATEGORY_USERS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_TYPE_CREATED,
                description="A new customer type was created.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        errors = defaultdict(list)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = CustomerTypeCreateErrorCode.REQUIRED.value
            errors["slug"].append(error)

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_type_created, instance)
