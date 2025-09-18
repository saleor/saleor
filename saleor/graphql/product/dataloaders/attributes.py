from collections import defaultdict

from ....attribute.models import (
    Attribute,
    AttributeProduct,
    AttributeVariant,
)
from ...attribute.dataloaders.attributes import AttributesByAttributeId
from ...core.dataloaders import DataLoader


class BaseProductAttributesByProductTypeIdLoader(DataLoader):
    """Loads product attributes by product type ID."""

    model_name = None
    extra_fields = None

    @staticmethod
    def filter_attributes(attributes: list[Attribute]) -> list[Attribute]:
        """Filter attributes based on custom logic, if needed."""
        return attributes

    def batch_load(self, keys):
        if not self.model_name:
            raise ValueError("Provide a model_name for this dataloader.")
        if not self.extra_fields:
            self.extra_fields = []

        product_type_attribute_pairs = (
            self.model_name.objects.using(self.database_connection_name)
            .filter(product_type_id__in=keys)
            .values_list("product_type_id", "attribute_id", *self.extra_fields)
        )

        def map_attributes(attributes):
            attributes = self.filter_attributes(attributes)
            attributes_map = {attr.id: attr for attr in attributes}

            product_type_to_attributes_map = defaultdict(list)
            for product_type_id, attr_id, *extra_fields in product_type_attribute_pairs:
                if attr_id in attributes_map:
                    # Only add attributes that are in the attributes_map to ensure
                    # that filtered attributes are respected.
                    product_type_to_attributes_map[product_type_id].append(
                        (attributes_map[attr_id], *extra_fields)
                    )
            return [
                product_type_to_attributes_map.get(product_type_id, [])
                for product_type_id in keys
            ]

        return (
            AttributesByAttributeId(self.context)
            .load_many({attr_id for _, attr_id, *_ in product_type_attribute_pairs})
            .then(map_attributes)
        )


class ProductAttributesAllByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    context_key = "product_attributes_all_by_producttype"
    model_name = AttributeProduct


class ProductAttributesVisibleInStorefrontByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    context_key = "product_attributes_visible_in_storefront_by_producttype"
    model_name = AttributeProduct

    @staticmethod
    def filter_attributes(attributes: list[Attribute]) -> list[Attribute]:
        return [attr for attr in attributes if attr and attr.visible_in_storefront]


class VariantAttributesAllByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    """Loads variant attributes by product type ID."""

    context_key = "variant_attributes_all_by_producttype"
    model_name = AttributeVariant
    extra_fields = ["variant_selection"]


class VariantAttributesVisibleInStorefrontByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    """Loads variant attributes by product type ID."""

    context_key = "variant_attributes_visible_in_storefront_by_producttype"
    model_name = AttributeVariant
    extra_fields = ["variant_selection"]

    @staticmethod
    def filter_attributes(attributes: list[Attribute]) -> list[Attribute]:
        return [attr for attr in attributes if attr and attr.visible_in_storefront]
