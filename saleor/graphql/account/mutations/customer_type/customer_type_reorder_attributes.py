import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....account import models
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import CustomerTypePermissions
from ....attribute.mutations import BaseReorderAttributesMutation
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerTypeReorderAttributesErrorCode
from ....core.inputs import ReorderInput
from ....core.types import Error, NonNullList
from ....core.utils.reordering import perform_reordering
from ...types import CustomerType


class CustomerTypeReorderAttributesError(Error):
    code = CustomerTypeReorderAttributesErrorCode(
        description="The error code.", required=True
    )
    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeReorderAttributes(BaseReorderAttributesMutation):
    customer_type = graphene.Field(
        CustomerType, description="Customer type from which attributes are reordered."
    )

    class Arguments:
        customer_type_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a customer type."
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description="The list of attribute reordering operations.",
        )

    class Meta:
        description = "Reorder the attributes of a customer type." + ADDED_IN_323
        doc_category = DOC_CATEGORY_USERS
        error_type_class = CustomerTypeReorderAttributesError
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        customer_type_id = data["customer_type_id"]
        pk = cls.get_global_id_or_error(
            customer_type_id, only_type=CustomerType, field="customer_type_id"
        )

        try:
            customer_type = models.CustomerType.objects.prefetch_related(
                "attributecustomertype"
            ).get(pk=pk)
        except ObjectDoesNotExist as e:
            raise ValidationError(
                {
                    "customer_type_id": ValidationError(
                        f"Couldn't resolve to a customer type: {customer_type_id}",
                        code=CustomerTypeReorderAttributesErrorCode.NOT_FOUND.value,
                    )
                }
            ) from e

        customer_attributes = customer_type.attributecustomertype.all()
        moves = data["moves"]

        try:
            operations = cls.prepare_operations(moves, customer_attributes)
        except ValidationError as e:
            e.code = CustomerTypeReorderAttributesErrorCode.NOT_FOUND.value
            raise ValidationError({"moves": e}) from e

        with traced_atomic_transaction():
            perform_reordering(customer_attributes, operations)

        return CustomerTypeReorderAttributes(customer_type=customer_type)
