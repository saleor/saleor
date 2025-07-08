from collections import defaultdict

from django.db.models import F, Window
from django.db.models.functions import RowNumber

from ...attribute.models import Attribute, AttributeValue
from ..core.dataloaders import DataLoader, DataLoaderWithLimit


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


class AttributeValuesByAttributeIdWithLimitLoader(
    DataLoaderWithLimit[int, list[AttributeValue]]
):
    context_key = "attributevalues_by_attribute"

    def batch_load(self, keys):
        attribute_values = (
            AttributeValue.objects.using(self.database_connection_name)
            .filter(attribute_id__in=keys)
            .annotate(
                row_num=Window(
                    expression=RowNumber(),
                    partition_by=F("attribute_id"),
                    order_by=F("id").asc(),
                )
            )
            .filter(row_num__lte=self.limit)
        )

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
