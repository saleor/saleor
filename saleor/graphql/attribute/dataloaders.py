from collections import defaultdict
from collections.abc import Iterable

from django.db.models import F, Window
from django.db.models.functions import RowNumber

from ...attribute.models import Attribute, AttributeValue
from ...attribute.models.page import AssignedPageAttributeValue
from ...attribute.models.product import AssignedProductAttributeValue
from ...attribute.models.product_variant import (
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
)
from ..core.dataloaders import DataLoader


class AttributeValuesByAttributeIdLoader(DataLoader[int, list[AttributeValue]]):
    context_key = "attributevalues_by_attribute"

    def batch_load(self, keys):
        attribute_values = AttributeValue.objects.using(
            self.database_connection_name
        ).filter(attribute_id__in=keys)
        attribute_to_attributevalues = defaultdict(list)
        for attribute_value in attribute_values.iterator(chunk_size=1000):
            attribute_to_attributevalues[attribute_value.attribute_id].append(
                attribute_value
            )
        return [attribute_to_attributevalues[attribute_id] for attribute_id in keys]


class AttributesByAttributeId(DataLoader[int, Attribute]):
    context_key = "attributes_by_id"

    def batch_load(self, keys):
        attributes = Attribute.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [attributes.get(key) for key in keys]


class AttributesBySlugLoader(DataLoader[str, Attribute]):
    context_key = "attributes_by_slug"

    def batch_load(self, keys):
        attributes = Attribute.objects.using(self.database_connection_name).in_bulk(
            keys, field_name="slug"
        )
        return [attributes.get(slug) for slug in keys]


class AttributeValueByIdLoader(DataLoader[int, AttributeValue]):
    context_key = "attributevalue_by_id"

    def batch_load(self, keys):
        attribute_values = AttributeValue.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [attribute_values.get(attribute_value_id) for attribute_value_id in keys]


PRODUCT_ID = int
PAGE_ID = int
VARIANT_ID = int
ATTRIBUTE_ID = int
LIMIT = int | None


class AttributeValuesByProductIdAndAttributeIdAndLimitLoader(
    DataLoader[tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]]
):
    context_key = "attribute_values_by_product_and_attribute"

    def batch_load(self, keys: Iterable[tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT]]):
        limit_map = defaultdict(list)
        for product_id, attribute_id, limit in keys:
            limit_map[limit].append((product_id, attribute_id))

        attribute_value_id_to_fetch_map: dict[
            tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT], list[int]
        ] = defaultdict(list)

        for limit, values in limit_map.items():
            product_ids = [val[0] for val in values]
            attribute_ids = [val[1] for val in values]

            assigned_attribute_values = AssignedProductAttributeValue.objects.using(
                self.database_connection_name
            ).annotate(attribute_id=F("value__attribute_id"))
            if limit is not None:
                assigned_attribute_values = assigned_attribute_values.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=[F("attribute_id"), F("product_id")],
                        order_by=["sort_order", "pk"],
                    )
                ).filter(row_num__lte=limit)

            assigned_attribute_values = assigned_attribute_values.filter(
                attribute_id__in=attribute_ids,
                product_id__in=product_ids,
            ).values_list("product_id", "value_id", "attribute_id")

            for product_id, value_id, attribute_id in assigned_attribute_values:
                attribute_value_id_to_fetch_map[
                    (product_id, attribute_id, limit)
                ].append(value_id)

        attribute_value_ids_to_fetch = set()
        for id_list in attribute_value_id_to_fetch_map.values():
            attribute_value_ids_to_fetch.update(id_list)

        def with_attribute_values(attribute_values: list[AttributeValue]):
            attribute_value_map = {av.id: av for av in attribute_values}
            response_data: defaultdict[
                tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]
            ] = defaultdict(list)
            for (
                product_id,
                attribute_id,
                limit,
            ), value_ids in attribute_value_id_to_fetch_map.items():
                for value_id in value_ids:
                    attr_val = attribute_value_map.get(value_id)
                    if not attr_val:
                        continue
                    response_data[(product_id, attribute_id, limit)].append(attr_val)
            return [response_data.get(key, []) for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(attribute_value_ids_to_fetch)
            .then(with_attribute_values)
        )


class AttributeValuesByPageIdAndAttributeIdAndLimitLoader(
    DataLoader[tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]]
):
    context_key = "attribute_values_by_page_and_attribute"

    def batch_load(self, keys: Iterable[tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT]]):
        limit_map = defaultdict(list)
        for page_id, attribute_id, limit in keys:
            limit_map[limit].append((page_id, attribute_id))

        attribute_value_id_to_fetch_map: dict[
            tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT], list[int]
        ] = defaultdict(list)

        for limit, values in limit_map.items():
            page_ids = [val[0] for val in values]
            attribute_ids = [val[1] for val in values]

            assigned_attribute_values = AssignedPageAttributeValue.objects.using(
                self.database_connection_name
            ).annotate(attribute_id=F("value__attribute_id"))
            if limit is not None:
                assigned_attribute_values = assigned_attribute_values.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=[F("attribute_id"), F("page_id")],
                        order_by=["sort_order", "pk"],
                    )
                ).filter(row_num__lte=limit)
            assigned_attribute_values = assigned_attribute_values.filter(
                attribute_id__in=attribute_ids,
                page_id__in=page_ids,
            ).values_list("page_id", "value_id", "attribute_id")

            for page_id, value_id, attribute_id in assigned_attribute_values:
                attribute_value_id_to_fetch_map[(page_id, attribute_id, limit)].append(
                    value_id
                )

        attribute_value_ids_to_fetch = set()
        for id_list in attribute_value_id_to_fetch_map.values():
            attribute_value_ids_to_fetch.update(id_list)

        def with_attribute_values(attribute_values: list[AttributeValue]):
            attribute_value_map = {av.id: av for av in attribute_values}
            response_data: defaultdict[
                tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]
            ] = defaultdict(list)
            for (
                page_id,
                attribute_id,
                limit,
            ), value_ids in attribute_value_id_to_fetch_map.items():
                for value_id in value_ids:
                    attr_val = attribute_value_map.get(value_id)
                    if not attr_val:
                        continue
                    response_data[(page_id, attribute_id, limit)].append(attr_val)
            return [response_data.get(key, []) for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(attribute_value_ids_to_fetch)
            .then(with_attribute_values)
        )


class AttributeValuesByVariantIdAndAttributeIdAndLimitLoader(
    DataLoader[tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]]
):
    context_key = "attribute_values_by_variant_and_attribute"

    def batch_load(self, keys: Iterable[tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT]]):
        limit_map = defaultdict(list)

        for variant_id, attribute_id, limit in keys:
            limit_map[limit].append((variant_id, attribute_id))

        attribute_value_id_to_fetch_map: dict[
            tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT], list[int]
        ] = defaultdict(list)

        for limit, values in limit_map.items():
            variant_ids = [val[0] for val in values]
            attribute_ids = [val[1] for val in values]

            assigned_variant_attributes = (
                AssignedVariantAttribute.objects.using(self.database_connection_name)
                .annotate(attribute_id=F("assignment__attribute_id"))
                .filter(
                    variant_id__in=variant_ids,
                    attribute_id__in=attribute_ids,
                )
                .values_list("variant_id", "id", "attribute_id")
            )
            assigned_variant_attributes_map = {
                id_: (variant_id, attribute_id)
                for variant_id, id_, attribute_id in assigned_variant_attributes
            }

            assigned_variant_values = AssignedVariantAttributeValue.objects.using(
                self.database_connection_name
            ).filter(assignment_id__in=assigned_variant_attributes_map.keys())
            if limit is not None:
                assigned_variant_values = assigned_variant_values.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=F("assignment_id"),
                        order_by=["sort_order", "pk"],
                    )
                ).filter(row_num__lte=limit)
            assigned_variant_values = assigned_variant_values.values_list(
                "value_id", "assignment_id"
            )

            for value_id, assignment_id in assigned_variant_values:
                if assignment_id not in assigned_variant_attributes_map:
                    continue
                variant_id, attribute_id = assigned_variant_attributes_map[
                    assignment_id
                ]
                attribute_value_id_to_fetch_map[
                    (variant_id, attribute_id, limit)
                ].append(value_id)

        attribute_value_ids_to_fetch = set()
        for id_list in attribute_value_id_to_fetch_map.values():
            attribute_value_ids_to_fetch.update(id_list)

        def with_attribute_values(attribute_values: list[AttributeValue]):
            attribute_value_map = {av.id: av for av in attribute_values}
            response_data: defaultdict[
                tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]
            ] = defaultdict(list)
            for (
                variant_id,
                attribute_id,
                limit,
            ), value_ids in attribute_value_id_to_fetch_map.items():
                for value_id in value_ids:
                    attr_val = attribute_value_map.get(value_id)
                    if not attr_val:
                        continue
                    response_data[(variant_id, attribute_id, limit)].append(attr_val)
            return [response_data.get(key, []) for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(attribute_value_ids_to_fetch)
            .then(with_attribute_values)
        )
