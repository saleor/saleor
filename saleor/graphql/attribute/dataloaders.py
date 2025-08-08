from collections import defaultdict

from django.db.models import F, Window
from django.db.models.functions import RowNumber

from ...attribute.models import Attribute, AttributeValue
from ...page.models import PageType
from ...product.models import ProductType
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


class AttributeReferenceProductTypesByAttributeIdLoader(
    DataLoaderWithLimit[int, list[ProductType]]
):
    context_key = "attributereferenceproducttypes_by_attribute"

    def batch_load(self, keys):
        ReferenceTypeModel = Attribute.reference_product_types.through
        reference_types = (
            ReferenceTypeModel.objects.using(self.database_connection_name)  # type: ignore[misc]
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
        product_types = ProductType.objects.using(
            self.database_connection_name
        ).in_bulk(reference_types.values_list("producttype_id", flat=True))
        reference_type_map = defaultdict(list)
        for reference_type in reference_types:
            product_type = product_types.get(reference_type.producttype_id)
            if product_type:
                reference_type_map[reference_type.attribute_id].append(product_type)

        return [reference_type_map.get(key, []) for key in keys]


class AttributeReferencePageTypesByAttributeIdLoader(
    DataLoaderWithLimit[int, list[PageType]]
):
    context_key = "attributereferencepagetypes_by_attribute"

    def batch_load(self, keys):
        ReferenceTypeModel = Attribute.reference_page_types.through
        reference_types = (
            ReferenceTypeModel.objects.using(self.database_connection_name)  # type: ignore[misc]
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
        page_types = PageType.objects.using(self.database_connection_name).in_bulk(
            reference_types.values_list("pagetype_id", flat=True)
        )
        reference_type_map = defaultdict(list)
        for reference_type in reference_types:
            page_type = page_types.get(reference_type.pagetype_id)
            if page_type:
                reference_type_map[reference_type.attribute_id].append(page_type)

        return [reference_type_map.get(key, []) for key in keys]
