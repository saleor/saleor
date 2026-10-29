from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....permission.enums import CustomerTypePermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerTypeUpdateErrorCode
from ....core.mutations import DeprecatedModelMutation
from ....core.types import Error
from ....core.utils import WebhookEventInfo
from ....core.validators import validate_slug_and_generate_if_needed
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import CustomerType
from .customer_type_create import (
    CustomerTypeCreateInput,
    CustomerTypeDefaultTransferMixin,
)


class CustomerTypeUpdateError(Error):
    code = CustomerTypeUpdateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeUpdateInput(CustomerTypeCreateInput):
    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeUpdate(CustomerTypeDefaultTransferMixin, DeprecatedModelMutation):
    class Arguments:
        id = graphene.ID(
            description="ID of the customer type to update.", required=True
        )
        input = CustomerTypeUpdateInput(
            description="Fields required to update a customer type.", required=True
        )

    class Meta:
        description = "Updates a customer type." + ADDED_IN_323
        model = models.CustomerType
        object_type = CustomerType
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)
        error_type_class = CustomerTypeUpdateError
        doc_category = DOC_CATEGORY_USERS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_TYPE_UPDATED,
                description="A customer type was updated.",
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
            error.code = CustomerTypeUpdateErrorCode.REQUIRED.value
            errors["slug"].append(error)

        if cleaned_input.get("is_default") is False and instance.is_default:
            errors["is_default"].append(
                ValidationError(
                    "The default flag cannot be unset. Mark another customer "
                    "type as the default instead.",
                    code=CustomerTypeUpdateErrorCode.CANNOT_UNSET_DEFAULT.value,
                )
            )

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_type_updated, instance)
