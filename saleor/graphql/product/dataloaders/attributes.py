from collections import defaultdict

from django.db.models import Exists, OuterRef
from promise import Promise

from ....attribute.models import (
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    Attribute,
    AttributeProduct,
    AttributeVariant,
)
from ....permission.enums import ProductPermissions
from ...attribute.dataloaders import AttributesByAttributeId, AttributeValueByIdLoader
from ...core.dataloaders import DataLoader
from ...utils import get_user_or_app_from_context
from .products import ProductByIdLoader, ProductVariantByIdLoader


class BaseProductAttributesByProductTypeIdLoader(DataLoader):
    """Loads product attributes by product type ID."""

    model_name = None
    extra_fields = None

    def get_queryset(self):
        raise NotImplementedError()

    def batch_load(self, keys):
        if not self.model_name:
            raise ValueError("Provide a model_name for this dataloader.")
        if not self.extra_fields:
            self.extra_fields = []

        qs = self.get_queryset()
        product_type_attribute_pairs = qs.filter(product_type_id__in=keys).values_list(
            "product_type_id", "attribute_id", *self.extra_fields
        )

        product_type_to_attributes_map = defaultdict(list)
        for product_type_id, attr_id, *extra_fields in product_type_attribute_pairs:
            product_type_to_attributes_map[product_type_id].append(
                (attr_id, *extra_fields)
            )

        def map_attributes(attributes):
            attributes_map = {attr.id: attr for attr in attributes}
            return [
                [
                    (attributes_map[attr_id], *extra_fields)
                    for attr_id, *extra_fields in product_type_to_attributes_map[
                        product_type_id
                    ]
                ]
                for product_type_id in keys
            ]

        return (
            AttributesByAttributeId(self.context)
            .load_many(set(attr_id for _, attr_id, *_ in product_type_attribute_pairs))
            .then(map_attributes)
        )


class ProductAttributesAllByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    context_key = "product_attributes_all_by_producttype"
    model_name = AttributeProduct

    def get_queryset(self):
        return self.model_name.objects.using(self.database_connection_name).all()


class ProductAttributesVisibleInStorefrontByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    context_key = "product_attributes_visible_in_storefront_by_producttype"
    model_name = AttributeProduct

    def get_queryset(self):
        return self.model_name.objects.using(self.database_connection_name).filter(
            Exists(
                Attribute.objects.filter(
                    pk=OuterRef("attribute_id"), visible_in_storefront=True
                ),
            ),
        )


class VariantAttributesAllByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    """Loads variant attributes by product type ID."""

    context_key = "variant_attributes_all_by_producttype"
    model_name = AttributeVariant
    extra_fields = ["variant_selection"]

    def get_queryset(self):
        return self.model_name.objects.using(self.database_connection_name).all()


class VariantAttributesVisibleInStorefrontByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    """Loads variant attributes by product type ID."""

    context_key = "variant_attributes_visible_in_storefront_by_producttype"
    model_name = AttributeVariant
    extra_fields = ["variant_selection"]

    def get_queryset(self):
        return self.model_name.objects.using(self.database_connection_name).filter(
            Exists(
                Attribute.objects.filter(
                    pk=OuterRef("attribute_id"), visible_in_storefront=True
                ),
            ),
        )


class AttributeVariantsByProductTypeIdLoader(DataLoader):
    context_key = "attributevariants_by_producttype"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(ProductPermissions.MANAGE_PRODUCTS)
        ):
            qs = AttributeVariant.objects.using(self.database_connection_name).all()
        else:
            qs = AttributeVariant.objects.using(self.database_connection_name).filter(
                attribute__visible_in_storefront=True
            )
        attribute_variants = qs.filter(product_type_id__in=keys)
        producttype_to_attributevariants = defaultdict(list)
        for attribute_variant in attribute_variants.iterator():
            producttype_to_attributevariants[attribute_variant.product_type_id].append(
                attribute_variant
            )
        return [producttype_to_attributevariants[key] for key in keys]


class AssignedVariantAttributesByProductVariantId(DataLoader):
    context_key = "assignedvariantattributes_by_productvariant"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(ProductPermissions.MANAGE_PRODUCTS)
        ):
            qs = AssignedVariantAttribute.objects.using(
                self.database_connection_name
            ).all()
        else:
            qs = AssignedVariantAttribute.objects.using(
                self.database_connection_name
            ).filter(assignment__attribute__visible_in_storefront=True)
        assigned_variant_attributes = qs.filter(variant_id__in=keys).select_related(
            "assignment__attribute"
        )
        variant_attributes = defaultdict(list)
        for assigned_variant_attribute in assigned_variant_attributes.iterator():
            variant_attributes[assigned_variant_attribute.variant_id].append(
                assigned_variant_attribute
            )
        return [variant_attributes[variant_id] for variant_id in keys]


class AttributeValuesByAssignedVariantAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assignedvariantattribute"

    def batch_load(self, keys):
        attribute_values = list(
            AssignedVariantAttributeValue.objects.using(self.database_connection_name)
            .filter(assignment_id__in=keys)
            .iterator()
        )
        value_ids = [a.value_id for a in attribute_values]

        def map_assignment_to_values(values):
            value_map = dict(zip(value_ids, values))
            assigned_variant_map = defaultdict(list)
            for attribute_value in attribute_values:
                assigned_variant_map[attribute_value.assignment_id].append(
                    value_map.get(attribute_value.value_id)
                )
            return [assigned_variant_map[key] for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(value_ids)
            .then(map_assignment_to_values)
        )


class BaseAttributeValuesByProductIdLoader(DataLoader):
    def get_product_attributes_dataloader(self):
        raise NotImplementedError()

    def batch_load(self, keys):
        # Using list + iterator is a small optimisation because iterator causes
        # the db to not store the whole resultset into the memory
        # https://docs.djangoproject.com/en/3.2/ref/models/querysets/#iterator
        attribute_values = list(
            AssignedProductAttributeValue.objects.using(self.database_connection_name)
            .filter(product_id__in=keys)
            .iterator()
        )
        value_ids = [a.value_id for a in attribute_values]

        def with_products(products):
            products = [product for product in products if product]
            product_type_ids = [p.product_type_id for p in products]

            def with_attributes_and_values(result):
                attribute_products, values = result
                product_type_attrubutes = dict(
                    zip(product_type_ids, attribute_products)
                )
                values_by_id_map = dict(zip(value_ids, values))
                assigned_product_map = defaultdict(list)

                for product in products:
                    product_values = [
                        values_by_id_map.get(product_value.value_id)
                        for product_value in attribute_values
                        if product_value.product_id == product.id
                    ]

                    attributes = product_type_attrubutes[product.product_type_id]
                    for attribute_tuple in attributes:
                        attribute = attribute_tuple[0]
                        values = [
                            value
                            for value in product_values
                            if value and value.attribute_id == attribute.id
                        ]
                        assigned_product_map[product.id].append(
                            {
                                "attribute": attribute,
                                "values": values,
                            }
                        )
                return [assigned_product_map[key] for key in keys]

            attributes = self.get_product_attributes_dataloader().load_many(
                product_type_ids
            )
            values = AttributeValueByIdLoader(self.context).load_many(value_ids)
            return Promise.all([attributes, values]).then(with_attributes_and_values)

        return ProductByIdLoader(self.context).load_many(keys).then(with_products)


class AttributeValuesAllByProductIdLoader(BaseAttributeValuesByProductIdLoader):
    context_key = "attributevalues_all_by_productid"

    def get_product_attributes_dataloader(self):
        return ProductAttributesAllByProductTypeIdLoader(self.context)


class AttributeValuesVisibleInStorefrontByProductIdLoader(
    BaseAttributeValuesByProductIdLoader
):
    context_key = "attributevalues_visible_in_storefront_by_productid"

    def get_product_attributes_dataloader(self):
        return ProductAttributesVisibleInStorefrontByProductTypeIdLoader(self.context)


class SelectedAttributesAllByProductIdLoader(DataLoader):
    context_key = "selectedattributes_all_by_product"

    def batch_load(self, product_ids):
        return AttributeValuesAllByProductIdLoader(self.context).load_many(product_ids)


class SelectedAttributesVisibleInStorefrontByProductIdLoader(DataLoader):
    context_key = "selectedattributes_visible_in_storefront_by_product"

    def batch_load(self, product_ids):
        return AttributeValuesVisibleInStorefrontByProductIdLoader(
            self.context
        ).load_many(product_ids)


class SelectedAttributesByProductVariantIdLoader(DataLoader):
    context_key = "selectedattributes_by_productvariant"

    def batch_load(self, keys):
        def with_variants_and_assigned_attributed(results):
            product_variants, variant_attributes = results
            product_ids = list({v.product_id for v in product_variants})
            assigned_variant_attribute_ids = [
                a.id for attrs in variant_attributes for a in attrs
            ]
            variant_attributes = dict(zip(keys, variant_attributes))

            def with_products_and_attribute_values(results):
                products, attribute_values = results
                product_type_ids = list({p.product_type_id for p in products})
                products = dict(zip(product_ids, products))
                attribute_values = dict(
                    zip(assigned_variant_attribute_ids, attribute_values)
                )

                def with_attribute_products(attribute_products):
                    attribute_ids = list(
                        {ap.attribute_id for aps in attribute_products for ap in aps}
                    )

                    attribute_products = dict(zip(product_type_ids, attribute_products))

                    def with_attributes(attributes):
                        id_to_attribute = dict(zip(attribute_ids, attributes))
                        selected_attributes_map = defaultdict(list)
                        for key, product_variant in zip(keys, product_variants):
                            product = products[product_variant.product_id]
                            assigned_producttype_attributes = attribute_products[
                                product.product_type_id
                            ]
                            assigned_variant_attributes = variant_attributes[key]
                            for (
                                assigned_producttype_attribute
                            ) in assigned_producttype_attributes:
                                variant_assignment = next(
                                    (
                                        apa
                                        for apa in assigned_variant_attributes
                                        if apa.assignment_id
                                        == assigned_producttype_attribute.id
                                    ),
                                    None,
                                )
                                attribute = id_to_attribute[
                                    assigned_producttype_attribute.attribute_id
                                ]
                                variant_selection = (
                                    assigned_producttype_attribute.variant_selection
                                )
                                if variant_assignment:
                                    values = attribute_values[variant_assignment.id]
                                else:
                                    values = []
                                selected_attributes_map[key].append(
                                    {
                                        "values": values,
                                        "attribute": attribute,
                                        "variant_selection": variant_selection,
                                    }
                                )
                        return [selected_attributes_map[key] for key in keys]

                    return (
                        AttributesByAttributeId(self.context)
                        .load_many(attribute_ids)
                        .then(with_attributes)
                    )

                return (
                    AttributeVariantsByProductTypeIdLoader(self.context)
                    .load_many(product_type_ids)
                    .then(with_attribute_products)
                )

            products = ProductByIdLoader(self.context).load_many(product_ids)
            attribute_values = AttributeValuesByAssignedVariantAttributeIdLoader(
                self.context
            ).load_many(assigned_variant_attribute_ids)

            return Promise.all([products, attribute_values]).then(
                with_products_and_attribute_values
            )

        product_variants = ProductVariantByIdLoader(self.context).load_many(keys)
        assigned_attributes = AssignedVariantAttributesByProductVariantId(
            self.context
        ).load_many(keys)

        return Promise.all([product_variants, assigned_attributes]).then(
            with_variants_and_assigned_attributed
        )
