from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from .....account import models as account_models
from .....attribute import AttributeType
from .....attribute import models as attribute_models
from .....permission.enums import CustomerTypePermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....attribute.types import Attribute
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerTypeAssignAttributesErrorCode
from ....core.mutations import BaseMutation
from ....core.types import Error, NonNullList
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import CustomerType

ATTRIBUTES_LIMIT = 100


class CustomerTypeAssignAttributesError(Error):
    code = CustomerTypeAssignAttributesErrorCode(
        description="The error code.", required=True
    )
    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeAssignAttributes(BaseMutation):
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
        error_type_class = CustomerTypeAssignAttributesError
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_TYPE_UPDATED,
                description="A customer type was updated.",
            ),
        ]

    @classmethod
    def clean_attributes(
        cls,
        errors: dict[str, list[ValidationError]],
        customer_type: account_models.CustomerType,
        attr_pks: list[int],
    ):
        """Ensure the attributes exist, are customer attributes, and are not assigned."""
        attr_type_by_pk = dict(
            attribute_models.Attribute.objects.filter(pk__in=attr_pks).values_list(
                "pk", "type"
            )
        )

        found_pks = {str(pk) for pk in attr_type_by_pk}
        missing_pks = [pk for pk in attr_pks if str(pk) not in found_pks]
        if missing_pks:
            missing_attributes_ids = [
                graphene.Node.to_global_id("Attribute", pk) for pk in missing_pks
            ]
            error = ValidationError(
                "Some of the attributes do not exist.",
                code=CustomerTypeAssignAttributesErrorCode.NOT_FOUND.value,
                params={"attributes": missing_attributes_ids},
            )
            errors["attribute_ids"].append(error)

        invalid_attributes_ids = [
            graphene.Node.to_global_id("Attribute", pk)
            for pk, attr_type in attr_type_by_pk.items()
            if attr_type != AttributeType.CUSTOMER_TYPE
        ]
        if invalid_attributes_ids:
            error = ValidationError(
                "Only customer attributes can be assigned.",
                code=CustomerTypeAssignAttributesErrorCode.INVALID.value,
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
                code=CustomerTypeAssignAttributesErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.value,
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
                        code=CustomerTypeAssignAttributesErrorCode.INVALID.value,
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

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_type_updated, customer_type)

        return cls(customer_type=customer_type)
