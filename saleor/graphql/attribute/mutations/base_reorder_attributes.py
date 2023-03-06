from typing import TYPE_CHECKING

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....core.tracing import traced_atomic_transaction
from ...core.inputs import ReorderInput
from ...core.mutations import BaseMutation
from ...core.utils.reordering import perform_reordering
from ..types import Attribute, AttributeValue

if TYPE_CHECKING:
    from django.db.models import QuerySet


class BaseReorderAttributesMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def prepare_operations(cls, moves: ReorderInput, attributes: "QuerySet"):
        """Prepare operations dict for reordering attributes.

        Operation dict format:
            key: attribute pk,
            value: sort_order value - relative sorting position of the attribute
        """
        attribute_ids = []
        sort_orders = []

        # resolve attribute moves
        for move_info in moves:
            attribute_ids.append(move_info.id)
            sort_orders.append(move_info.sort_order)

        attr_pks = cls.get_global_ids_or_error(attribute_ids, Attribute)
        attr_pks = [int(pk) for pk in attr_pks]

        attributes_m2m = attributes.filter(attribute_id__in=attr_pks)

        if attributes_m2m.count() != len(attr_pks):
            attribute_pks = attributes_m2m.values_list("attribute_id", flat=True)
            invalid_attrs = set(attr_pks) - set(attribute_pks)
            invalid_attr_ids = [
                graphene.Node.to_global_id("Attribute", attr_pk)
                for attr_pk in invalid_attrs
            ]
            raise ValidationError(
                "Couldn't resolve to an attribute.",
                params={"attributes": invalid_attr_ids},
            )

        attributes_m2m = list(attributes_m2m)
        attributes_m2m.sort(
            key=lambda e: attr_pks.index(e.attribute.pk)
        )  # preserve order in pks

        operations = {
            attribute.pk: sort_order
            for attribute, sort_order in zip(attributes_m2m, sort_orders)
        }

        return operations


class BaseReorderAttributeValuesMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def perform(
        cls,
        instance_id: str,
        instance_type: str,
        data: dict,
        assignment_lookup: str,
        error_code_enum,
    ):
        attribute_id = data["attribute_id"]
        moves = data["moves"]

        instance = cls.get_instance(instance_id)
        attribute_assignment = cls.get_attribute_assignment(
            instance, instance_type, attribute_id, error_code_enum
        )
        values_m2m = getattr(attribute_assignment, assignment_lookup)

        try:
            operations = cls.prepare_operations(moves, values_m2m)
        except ValidationError as error:
            error.code = error_code_enum.NOT_FOUND.value
            raise ValidationError({"moves": error})

        with traced_atomic_transaction():
            perform_reordering(values_m2m, operations)

        return instance

    @staticmethod
    def get_instance(instance_id: str):
        pass

    @classmethod
    def get_attribute_assignment(
        cls, instance, instance_type, attribute_id: str, error_code_enum
    ):
        attribute_pk = cls.get_global_id_or_error(
            attribute_id, only_type=Attribute, field="attribute_id"
        )

        try:
            attribute_assignment = instance.attributes.prefetch_related("values").get(
                assignment__attribute_id=attribute_pk  # type: ignore
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "attribute_id": ValidationError(
                        f"Couldn't resolve to a {instance_type} "
                        f"attribute: {attribute_id}.",
                        code=error_code_enum.NOT_FOUND.value,
                    )
                }
            )
        return attribute_assignment

    @classmethod
    def prepare_operations(cls, moves: ReorderInput, values: "QuerySet"):
        """Prepare operations dict for reordering attribute values.

        Operation dict format:
            key: attribute value pk,
            value: sort_order value - relative sorting position of the attribute
        """
        value_ids = []
        sort_orders = []

        # resolve attribute moves
        for move_info in moves:
            value_ids.append(move_info.id)
            sort_orders.append(move_info.sort_order)

        values_pks = cls.get_global_ids_or_error(value_ids, AttributeValue)
        values_pks = [int(pk) for pk in values_pks]

        values_m2m = values.filter(value_id__in=values_pks)

        if values_m2m.count() != len(values_pks):
            pks = values_m2m.values_list("value_id", flat=True)
            invalid_values = set(values_pks) - set(pks)
            invalid_ids = [
                graphene.Node.to_global_id("AttributeValue", val_pk)
                for val_pk in invalid_values
            ]
            raise ValidationError(
                "Couldn't resolve to an attribute value.",
                params={"values": invalid_ids},
            )

        values_m2m = list(values_m2m)
        values_m2m.sort(
            key=lambda e: values_pks.index(e.value_id)
        )  # preserve order in pks

        operations = {
            value.pk: sort_order for value, sort_order in zip(values_m2m, sort_orders)
        }

        return operations
