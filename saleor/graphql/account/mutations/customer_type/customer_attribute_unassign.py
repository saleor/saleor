import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import CustomerTypePermissions
from ....attribute.types import Attribute
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerAttributeUnassignErrorCode
from ....core.mutations import BaseMutation
from ....core.types import Error, NonNullList
from ....utils import resolve_global_ids_to_primary_keys
from ...types import CustomerType

ATTRIBUTES_LIMIT = 100


class CustomerAttributeUnassignError(Error):
    code = CustomerAttributeUnassignErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerAttributeUnassign(BaseMutation):
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
        error_type_class = CustomerAttributeUnassignError
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)

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
                        code=CustomerAttributeUnassignErrorCode.INVALID.value,
                    )
                }
            )

        customer_type = cls.get_node_or_error(
            info, customer_type_id, only_type=CustomerType, field="customer_type_id"
        )

        _, attr_pks = resolve_global_ids_to_primary_keys(attribute_ids, Attribute)

        customer_type.customer_attributes.remove(*attr_pks)

        return cls(customer_type=customer_type)
