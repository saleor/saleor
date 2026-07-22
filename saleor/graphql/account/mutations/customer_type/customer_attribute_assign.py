from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from .....account import models as account_models
from .....attribute import AttributeType
from .....attribute import models as attribute_models
from .....permission.enums import CustomerTypePermissions
from ....attribute.types import Attribute
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerAttributeAssignErrorCode
from ....core.mutations import BaseMutation
from ....core.types import Error, NonNullList
from ...types import CustomerType

ATTRIBUTES_LIMIT = 100


class CustomerAttributeAssignError(Error):
    code = CustomerAttributeAssignErrorCode(
        description="The error code.", required=True
    )
    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerAttributeAssign(BaseMutation):
    customer_type = graphene.Field(
        CustomerType, description="The updated customer type."
    )

    class Arguments:
        customer_type_id = graphene.ID(
            required=True,
            description="ID of the customer type to assign the attributes to.",
        )
        attribute_ids = NonNullList(
            graphene.ID,
            required=True,
            description=(
                "The IDs of the attributes to assign. "
                f"Maximum of {ATTRIBUTES_LIMIT} items."
            ),
        )

    class Meta:
        description = "Assign attributes to a given customer type." + ADDED_IN_323
        doc_category = DOC_CATEGORY_USERS
        error_type_class = CustomerAttributeAssignError
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)

    @classmethod
    def clean_attributes(
        cls,
        errors: dict[str, list[ValidationError]],
        customer_type: account_models.CustomerType,
        attr_pks: list[int],
    ):
        """Ensure the attributes are customer attributes and are not yet assigned."""
        invalid_attributes = attribute_models.Attribute.objects.filter(
            pk__in=attr_pks
        ).exclude(type=AttributeType.CUSTOMER_TYPE)

        if invalid_attributes:
            invalid_attributes_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in invalid_attributes
            ]
            error = ValidationError(
                "Only customer attributes can be assigned.",
                code=CustomerAttributeAssignErrorCode.INVALID.value,
                params={"attributes": invalid_attributes_ids},
            )
            errors["attribute_ids"].append(error)

        assigned_attrs = (
            attribute_models.Attribute.objects.get_assigned_customer_type_attributes(
                customer_type.pk
            ).filter(pk__in=attr_pks)
        )

        if assigned_attrs:
            assigned_attributes_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in assigned_attrs
            ]
            error = ValidationError(
                "Some of the attributes have been already assigned to this "
                "customer type.",
                code=CustomerAttributeAssignErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.value,
                params={"attributes": assigned_attributes_ids},
            )
            errors["attribute_ids"].append(error)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, attribute_ids, customer_type_id
    ):
        if len(attribute_ids) > ATTRIBUTES_LIMIT:
            raise ValidationError(
                {
                    "attribute_ids": ValidationError(
                        f"Cannot assign more than {ATTRIBUTES_LIMIT} attributes "
                        "in a single mutation.",
                        code=CustomerAttributeAssignErrorCode.INVALID.value,
                    )
                }
            )

        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)

        customer_type = cls.get_node_or_error(
            info, customer_type_id, only_type=CustomerType, field="customer_type_id"
        )

        attr_pks = cls.get_global_ids_or_error(
            attribute_ids, Attribute, field="attribute_ids"
        )

        cls.clean_attributes(errors, customer_type, attr_pks)

        if errors:
            raise ValidationError(errors)

        customer_type.customer_attributes.add(*attr_pks)

        return cls(customer_type=customer_type)
