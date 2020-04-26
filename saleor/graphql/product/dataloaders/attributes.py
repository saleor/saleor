from collections import defaultdict

from promise import Promise

from ....core.permissions import ProductPermissions
from ....product.models import (
    AssignedProductAttribute,
    AssignedVariantAttribute,
    Attribute,
    AttributeProduct,
    AttributeValue,
    AttributeVariant,
)
from ...core.dataloaders import DataLoader
from .products import ProductByIdLoader, ProductVariantByIdLoader


class AttributeValuesByAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_attribute"

    def batch_load(self, keys):
        attribute_values = AttributeValue.objects.filter(attribute_id__in=keys)
        attribute_to_attributevalues = defaultdict(list)
        for attribute_value in attribute_values.iterator():
            attribute_to_attributevalues[attribute_value.attribute_id].append(
                attribute_value
            )
        return [attribute_to_attributevalues[attribute_id] for attribute_id in keys]


class AttributesByAttributeId(DataLoader):
    context_key = "attributes_by_id"

    def batch_load(self, keys):
        attributes = Attribute.objects.in_bulk(keys)
        return [attributes.get(key) for key in keys]


class AttributeProductsByProductTypeIdLoader(DataLoader):
    context_key = "attributeproducts_by_producttype"

    def batch_load(self, keys):
        user = self.user
        if user.is_active and user.has_perm(ProductPermissions.MANAGE_PRODUCTS):
            qs = AttributeProduct.objects.all()
        else:
            qs = AttributeProduct.objects.filter(attribute__visible_in_storefront=True)
        attribute_products = qs.filter(product_type_id__in=keys)
        producttype_to_attributeproducts = defaultdict(list)
        for attribute_product in attribute_products:
            producttype_to_attributeproducts[attribute_product.product_type_id].append(
                attribute_product
            )
        return [producttype_to_attributeproducts[key] for key in keys]


class AttributeVariantsByProductTypeIdLoader(DataLoader):
    context_key = "attributevariants_by_producttype"

    def batch_load(self, keys):
        user = self.user
        if user.is_active and user.has_perm(ProductPermissions.MANAGE_PRODUCTS):
            qs = AttributeVariant.objects.all()
        else:
            qs = AttributeVariant.objects.filter(attribute__visible_in_storefront=True)
        attribute_variants = qs.filter(product_type_id__in=keys)
        producttype_to_attributevariants = defaultdict(list)
        for attribute_variant in attribute_variants:
            producttype_to_attributevariants[attribute_variant.product_type_id].append(
                attribute_variant
            )
        return [producttype_to_attributevariants[key] for key in keys]


class AssignedProductAttributesByProductIdLoader(DataLoader):
    context_key = "assignedproductattributes_by_product"

    def batch_load(self, keys):
        user = self.user
        if user.is_active and user.has_perm(ProductPermissions.MANAGE_PRODUCTS):
            qs = AssignedProductAttribute.objects.all()
        else:
            qs = AssignedProductAttribute.objects.filter(
                assignment__attribute__visible_in_storefront=True
            )
        assigned_product_attributes = qs.filter(product_id__in=keys)
        product_to_assignedproductattributes = defaultdict(list)
        for assigned_product_attribute in assigned_product_attributes:
            product_to_assignedproductattributes[
                assigned_product_attribute.product_id
            ].append(assigned_product_attribute)
        return [product_to_assignedproductattributes[product_id] for product_id in keys]


class AssignedVariantAttributesByProductVariantId(DataLoader):
    context_key = "assignedvariantattributes_by_productvariant"

    def batch_load(self, keys):
        user = self.user
        if user.is_active and user.has_perm(ProductPermissions.MANAGE_PRODUCTS):
            qs = AssignedVariantAttribute.objects.all()
        else:
            qs = AssignedVariantAttribute.objects.filter(
                assignment__attribute__visible_in_storefront=True
            )
        assigned_variant_attributes = qs.filter(variant_id__in=keys).select_related(
            "assignment__attribute"
        )
        variant_attributes = defaultdict(list)
        for assigned_variant_attribute in assigned_variant_attributes:
            variant_attributes[assigned_variant_attribute.variant_id].append(
                assigned_variant_attribute
            )
        return [variant_attributes[variant_id] for variant_id in keys]


class AttributeValueByIdLoader(DataLoader):
    context_key = "attributevalue_by_id"

    def batch_load(self, keys):
        attribute_values = AttributeValue.objects.in_bulk(keys)
        return [attribute_values.get(attribute_value_id) for attribute_value_id in keys]


class AttributeValuesByAssignedProductAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assignedproductattribute"

    def batch_load(self, keys):
        AttributeAssignment = AttributeValue.assignedproductattribute_set.through
        attribute_values = AttributeAssignment.objects.filter(
            assignedproductattribute_id__in=keys
        )
        value_ids = [a.attributevalue_id for a in attribute_values]

        def map_assignment_to_values(values):
            value_map = dict(zip(value_ids, values))
            assigned_product_map = defaultdict(list)
            for attribute_value in attribute_values:
                assigned_product_map[
                    attribute_value.assignedproductattribute_id
                ].append(value_map.get(attribute_value.attributevalue_id))
            return [
                sorted(assigned_product_map[key], key=lambda v: (v.sort_order, v.id))
                for key in keys
            ]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(value_ids)
            .then(map_assignment_to_values)
        )


class AttributeValuesByAssignedVariantAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assignedvariantattribute"

    def batch_load(self, keys):
        AttributeAssignment = AttributeValue.assignedvariantattribute_set.through
        attribute_values = AttributeAssignment.objects.filter(
            assignedvariantattribute_id__in=keys
        )
        value_ids = [a.attributevalue_id for a in attribute_values]

        def map_assignment_to_values(values):
            value_map = dict(zip(value_ids, values))
            assigned_variant_map = defaultdict(list)
            for attribute_value in attribute_values:
                assigned_variant_map[
                    attribute_value.assignedvariantattribute_id
                ].append(value_map.get(attribute_value.attributevalue_id))
            return [
                sorted(assigned_variant_map[key], key=lambda v: (v.sort_order, v.id))
                for key in keys
            ]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(value_ids)
            .then(map_assignment_to_values)
        )


class SelectedAttributesByProductIdLoader(DataLoader):
    context_key = "selectedattributes_by_product"

    def batch_load(self, keys):
        def with_products_and_assigned_attributed(result):
            products, product_attributes = result
            assigned_product_attribute_ids = [
                a.id for attrs in product_attributes for a in attrs
            ]
            product_type_ids = list({p.product_type_id for p in products})
            product_attributes = dict(zip(keys, product_attributes))

            def with_attributeproducts_and_values(result):
                attribute_products, attribute_values = result
                attribute_ids = list(
                    {ap.attribute_id for aps in attribute_products for ap in aps}
                )
                attribute_products = dict(zip(product_type_ids, attribute_products))
                attribute_values = dict(
                    zip(assigned_product_attribute_ids, attribute_values)
                )

                def with_attributes(attributes):
                    id_to_attribute = dict(zip(attribute_ids, attributes))
                    selected_attributes_map = defaultdict(list)
                    for key, product in zip(keys, products):
                        assigned_producttype_attributes = attribute_products[
                            product.product_type_id
                        ]
                        assigned_product_attributes = product_attributes[key]
                        for (
                            assigned_producttype_attribute
                        ) in assigned_producttype_attributes:
                            product_assignment = next(
                                (
                                    apa
                                    for apa in assigned_product_attributes
                                    if apa.assignment_id
                                    == assigned_producttype_attribute.id
                                ),
                                None,
                            )
                            attribute = id_to_attribute[
                                assigned_producttype_attribute.attribute_id
                            ]
                            if product_assignment:
                                values = attribute_values[product_assignment.id]
                            else:
                                values = []
                            selected_attributes_map[key].append(
                                {"values": values, "attribute": attribute}
                            )
                    return [selected_attributes_map[key] for key in keys]

                return (
                    AttributesByAttributeId(self.context)
                    .load_many(attribute_ids)
                    .then(with_attributes)
                )

            attribute_products = AttributeProductsByProductTypeIdLoader(
                self.context
            ).load_many(product_type_ids)
            attribute_values = AttributeValuesByAssignedProductAttributeIdLoader(
                self.context
            ).load_many(assigned_product_attribute_ids)
            return Promise.all([attribute_products, attribute_values]).then(
                with_attributeproducts_and_values
            )

        products = ProductByIdLoader(self.context).load_many(keys)
        assigned_attributes = AssignedProductAttributesByProductIdLoader(
            self.context
        ).load_many(keys)

        return Promise.all([products, assigned_attributes]).then(
            with_products_and_assigned_attributed
        )


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
                                if variant_assignment:
                                    values = attribute_values[variant_assignment.id]
                                else:
                                    values = []
                                selected_attributes_map[key].append(
                                    {"values": values, "attribute": attribute}
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
