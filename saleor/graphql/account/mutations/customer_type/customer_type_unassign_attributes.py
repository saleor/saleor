import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import CustomerTypePermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....attribute.types import Attribute
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerTypeUnassignAttributesErrorCode
from ....core.mutations import BaseMutation
from ....core.types import Error, NonNullList
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....utils import resolve_global_ids_to_primary_keys
from ...types import CustomerType

ATTRIBUTES_LIMIT = 100


class CustomerTypeUnassignAttributesError(Error):
    code = CustomerTypeUnassignAttributesErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeUnassignAttributes(BaseMutation):
    customer_type = graphene.Field(
        CustomerType, description="The updated customer type."
    )

    class Arguments:
        customer_type_id = graphene.ID(
            required=True,
            description=(
                "ID of the customer type from which the attributes should be "
                "unassigned."
            ),
        )
        attribute_ids = NonNullList(
            graphene.ID,
            required=True,
            description=(
                "The IDs of the attributes to unassign. "
                f"Maximum of {ATTRIBUTES_LIMIT} items."
            ),
        )

    class Meta:
        description = (
            "Unassign attributes from a given customer type. Values already "
            "assigned to users are kept in the database, but are hidden until "
            "the attribute is assigned to the user's customer type again."
            + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = CustomerTypeUnassignAttributesError
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_TYPE_UPDATED,
                description="A customer type was updated.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, attribute_ids, customer_type_id
    ):
        if len(attribute_ids) > ATTRIBUTES_LIMIT:
            raise ValidationError(
                {
                    "attribute_ids": ValidationError(
                        f"Cannot unassign more than {ATTRIBUTES_LIMIT} attributes "
                        "in a single mutation.",
                        code=CustomerTypeUnassignAttributesErrorCode.INVALID.value,
                    )
                }
            )

        customer_type = cls.get_node_or_error(
            info, customer_type_id, only_type=CustomerType, field="customer_type_id"
        )

        _, attr_pks = resolve_global_ids_to_primary_keys(attribute_ids, Attribute)

        customer_type.customer_attributes.remove(*attr_pks)

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_type_updated, customer_type)

        return cls(customer_type=customer_type)
