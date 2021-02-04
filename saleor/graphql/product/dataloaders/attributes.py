from collections import defaultdict

from promise import Promise

from ....attribute.models import (
    AssignedCategoryAttribute,
    AssignedCategoryAttributeValue,
    AssignedProductAttribute,
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    AttributeCategory,
    AttributeProduct,
    AttributeVariant,
)
from ....core.permissions import ProductPermissions, SitePermissions
from ...attribute.dataloaders import AttributesByAttributeId, AttributeValueByIdLoader
from ...core.dataloaders import DataLoader
from ...utils import get_user_or_app_from_context
from .products import ProductByIdLoader, ProductVariantByIdLoader


class BaseProductAttributesByProductTypeIdLoader(DataLoader):
    """Loads product attributes by product type ID."""

    context_key = "product_attributes_by_producttype"
    model_name = None

    def batch_load(self, keys):
        if not self.model_name:
            raise ValueError("Provide a model_name for this dataloader.")

        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
            qs = self.model_name.objects.all()
        else:
            qs = self.model_name.objects.filter(attribute__visible_in_storefront=True)
        product_type_attribute_pairs = qs.filter(product_type_id__in=keys).values_list(
            "product_type_id", "attribute_id"
        )

        product_type_to_attributes_map = defaultdict(list)
        for product_type_id, attr_id in product_type_attribute_pairs:
            product_type_to_attributes_map[product_type_id].append(attr_id)

        def map_attributes(attributes):
            attributes_map = {attr.id: attr for attr in attributes}
            return [
                [
                    attributes_map[attr_id]
                    for attr_id in product_type_to_attributes_map[product_type_id]
                ]
                for product_type_id in keys
            ]

        return (
            AttributesByAttributeId(self.context)
            .load_many(set(attr_id for _, attr_id in product_type_attribute_pairs))
            .then(map_attributes)
        )


class ProductAttributesByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    """Loads product attributes by product type ID."""

    context_key = "product_attributes_by_producttype"
    model_name = AttributeProduct


class VariantAttributesByProductTypeIdLoader(
    BaseProductAttributesByProductTypeIdLoader
):
    """Loads variant attributes by product type ID."""

    context_key = "variant_attributes_by_producttype"
    model_name = AttributeVariant


class AttributeProductsByProductTypeIdLoader(DataLoader):
    """Loads AttributeProduct objects by product type ID."""

    context_key = "attributeproducts_by_producttype"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
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
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
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


class AttributeCategoriesBySiteSettingsIdLoader(DataLoader):
    """Loads AttributeCategory objects by site settings type ID."""

    context_key = "attributecategories_by_site_settings"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(SitePermissions.MANAGE_SETTINGS):
            qs = AttributeCategory.objects.all()
        else:
            qs = AttributeCategory.objects.filter(attribute__visible_in_storefront=True)
        attribute_categories = qs.filter(site_settings_id__in=keys)
        sitesettings_to_attributecategories = defaultdict(list)
        for attribute_category in attribute_categories:
            sitesettings_to_attributecategories[
                attribute_category.site_settings_id
            ].append(attribute_category)
        return [sitesettings_to_attributecategories[key] for key in keys]


class AssignedProductAttributesByProductIdLoader(DataLoader):
    context_key = "assignedproductattributes_by_product"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
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
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
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


class AssignedCategoryAttributesByCategoryIdLoader(DataLoader):
    context_key = "assignedcategoryattributes_by_category"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
            qs = AssignedCategoryAttribute.objects.all()
        else:
            qs = AssignedCategoryAttribute.objects.filter(
                assignment__attribute__visible_in_storefront=True
            )
        assigned_category_attributes = qs.filter(category_id__in=keys)
        category_to_assignedcategoryattributes = defaultdict(list)
        for assigned_category_attribute in assigned_category_attributes:
            category_to_assignedcategoryattributes[
                assigned_category_attribute.category_id
            ].append(assigned_category_attribute)
        return [
            category_to_assignedcategoryattributes[category_id] for category_id in keys
        ]


class AttributeValuesByAssignedProductAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assignedproductattribute"

    def batch_load(self, keys):
        attribute_values = AssignedProductAttributeValue.objects.filter(
            assignment_id__in=keys
        )
        value_ids = [a.value_id for a in attribute_values]

        def map_assignment_to_values(values):
            value_map = dict(zip(value_ids, values))
            assigned_product_map = defaultdict(list)
            for attribute_value in attribute_values:
                assigned_product_map[attribute_value.assignment_id].append(
                    value_map.get(attribute_value.value_id)
                )
            return [assigned_product_map[key] for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(value_ids)
            .then(map_assignment_to_values)
        )


class AttributeValuesByAssignedVariantAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assignedvariantattribute"

    def batch_load(self, keys):
        attribute_values = AssignedVariantAttributeValue.objects.filter(
            assignment_id__in=keys
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


class AttributeValuesByAssignedCategoryAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assignedcategoryattribute"

    def batch_load(self, keys):
        attribute_values = AssignedCategoryAttributeValue.objects.filter(
            assignment_id__in=keys
        )
        value_ids = [a.value_id for a in attribute_values]

        def map_assignment_to_values(values):
            value_map = dict(zip(value_ids, values))
            assigned_category_map = defaultdict(list)
            for attribute_value in attribute_values:
                assigned_category_map[attribute_value.assignment_id].append(
                    value_map.get(attribute_value.value_id)
                )
            return [assigned_category_map[key] for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(value_ids)
            .then(map_assignment_to_values)
        )


class SelectedAttributesByProductIdLoader(DataLoader):
    context_key = "selectedattributes_by_product"

    def batch_load(self, keys):
        def with_products_and_assigned_attributes(result):
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
            with_products_and_assigned_attributes
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


class SelectedAttributesByCategoryIdLoader(DataLoader):
    context_key = "selectedattributes_by_category"

    def batch_load(self, keys):
        def with_categories_and_assigned_attributes(category_attributes):
            assigned_category_attribute_ids = [
                a.id for attrs in category_attributes for a in attrs
            ]
            site_settings_id = self.context.site.settings.id
            category_attributes = dict(zip(keys, category_attributes))

            def with_attributecategories_and_values(result):
                attribute_categories, attribute_values = result
                attribute_ids = list({ap.attribute_id for ap in attribute_categories})
                attribute_values = dict(
                    zip(assigned_category_attribute_ids, attribute_values)
                )

                def with_attributes(attributes):
                    id_to_attribute = dict(zip(attribute_ids, attributes))
                    selected_attributes_map = defaultdict(list)
                    assigned_sitesettings_attributes = attribute_categories
                    for key in keys:
                        assigned_category_attributes = category_attributes[key]
                        for (
                            assigned_sitesetting_attribute
                        ) in assigned_sitesettings_attributes:
                            category_assignment = next(
                                (
                                    apa
                                    for apa in assigned_category_attributes
                                    if apa.assignment_id
                                    == assigned_sitesetting_attribute.id
                                ),
                                None,
                            )
                            attribute = id_to_attribute[
                                assigned_sitesetting_attribute.attribute_id
                            ]
                            if category_assignment:
                                values = attribute_values[category_assignment.id]
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

            attribute_categories = AttributeCategoriesBySiteSettingsIdLoader(
                self.context
            ).load(site_settings_id)
            attribute_values = AttributeValuesByAssignedCategoryAttributeIdLoader(
                self.context
            ).load_many(assigned_category_attribute_ids)
            return Promise.all([attribute_categories, attribute_values]).then(
                with_attributecategories_and_values
            )

        return (
            AssignedCategoryAttributesByCategoryIdLoader(self.context)
            .load_many(keys)
            .then(with_categories_and_assigned_attributes)
        )
