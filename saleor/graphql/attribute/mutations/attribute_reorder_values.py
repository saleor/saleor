import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....attribute import models as models
from ....attribute.error_codes import AttributeErrorCode
from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductTypePermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ...core.inputs import ReorderInput
from ...core.mutations import BaseMutation
from ...core.types import AttributeError, NonNullList
from ...core.utils import WebhookEventInfo
from ...core.utils.reordering import perform_reordering
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Attribute, AttributeValue


class AttributeReorderValues(BaseMutation):
    attribute = graphene.Field(
        Attribute, description="Attribute from which values are reordered."
    )

    class Meta:
        description = "Reorder the values of an attribute."
        doc_category = DOC_CATEGORY_ATTRIBUTES
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED,
                description="An attribute value was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_UPDATED,
                description="An attribute was updated.",
            ),
        ]

    class Arguments:
        attribute_id = graphene.Argument(
            graphene.ID, required=True, description="ID of an attribute."
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description="The list of reordering operations for given attribute values.",
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, attribute_id, moves
    ):
        pk = cls.get_global_id_or_error(
            attribute_id, only_type=Attribute, field="attribute_id"
        )

        try:
            attribute = models.Attribute.objects.prefetch_related("values").get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "attribute_id": ValidationError(
                        f"Couldn't resolve to an attribute: {attribute_id}",
                        code=AttributeErrorCode.NOT_FOUND.value,
                    )
                }
            )

        values_m2m = attribute.values.all()
        operations = {}

        # Resolve the values
        for move_info in moves:
            value_pk = cls.get_global_id_or_error(
                move_info.id, only_type=AttributeValue, field="moves"
            )

            try:
                m2m_info = values_m2m.get(pk=int(value_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to an attribute value: {move_info.id}",
                            code=AttributeErrorCode.NOT_FOUND.value,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with traced_atomic_transaction():
            perform_reordering(values_m2m, operations)
        attribute.refresh_from_db(fields=["values"])
        manager = get_plugin_manager_promise(info.context).get()
        events_list = [v for v in values_m2m if v.id in operations.keys()]
        for value in events_list:
            cls.call_event(manager.attribute_value_updated, value)
        cls.call_event(manager.attribute_updated, attribute)

        return AttributeReorderValues(attribute=attribute)
