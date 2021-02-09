from collections import defaultdict

from promise import Promise

from ....attribute.models import (
    AssignedCategoryAttribute,
    AssignedCategoryAttributeValue,
    AssignedCollectionAttribute,
    AssignedCollectionAttributeValue,
    AssignedProductAttribute,
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    AttributeCategory,
    AttributeCollection,
    AttributeProduct,
    AttributeVariant,
)
from ....core.permissions import PageTypePermissions, ProductPermissions
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


class BaseAttributeByProductTypeIdLoader(DataLoader):
    context_key = "attribute_by_producttype"
    model = None

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
            qs = self.model.objects.all()
        else:
            qs = self.model.objects.filter(attribute__visible_in_storefront=True)
        attributes = qs.filter(product_type_id__in=keys)
        producttype_to_attributes = defaultdict(list)
        for attribute in attributes:
            producttype_to_attributes[attribute.product_type_id].append(attribute)
        return [producttype_to_attributes[key] for key in keys]


class AttributeProductsByProductTypeIdLoader(BaseAttributeByProductTypeIdLoader):
    """Loads AttributeProduct objects by product type ID."""

    context_key = "attributeproducts_by_producttype"
    model = AttributeProduct


class AttributeVariantsByProductTypeIdLoader(BaseAttributeByProductTypeIdLoader):
    context_key = "attributevariants_by_producttype"
    model = AttributeVariant


class BaseAttributeBySiteSettingsIdLoader(DataLoader):
    context_key = "attribute_by_sitesettings"
    model = None

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES
        ):
            qs = self.model.objects.all()
        else:
            qs = self.model.objects.filter(attribute__visible_in_storefront=True)
        attributes = qs.filter(site_settings_id__in=keys)
        sitesettings_to_attributes = defaultdict(list)
        for attribute in attributes:
            sitesettings_to_attributes[attribute.site_settings_id].append(attribute)
        return [sitesettings_to_attributes[key] for key in keys]


class AttributeCategoriesBySiteSettingsIdLoader(BaseAttributeBySiteSettingsIdLoader):
    """Loads AttributeCategory objects by site settings type ID."""

    context_key = "attributecategories_by_site_settings"
    model = AttributeCategory


class AttributeCollectionsBySiteSettingsIdLoader(BaseAttributeBySiteSettingsIdLoader):
    """Loads AttributeCollection objects by site settings type ID."""

    context_key = "attributecollections_by_site_settings"
    model = AttributeCollection


class BaseAssignedAttributesByInstanceIdLoader(DataLoader):
    context_key = "assignedattributes_by_id"
    assigned_attr_model = None
    model_name = None

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if requestor.is_active and requestor.has_perm(
            ProductPermissions.MANAGE_PRODUCTS
        ):
            qs = self.assigned_attr_model.objects.all()
        else:
            qs = self.assigned_attr_model.objects.filter(
                assignment__attribute__visible_in_storefront=True
            )
        filter = {f"{self.model_name}_id__in": keys}
        assigned_attributes = qs.filter(**filter)
        instance_to_assignedattributes = defaultdict(list)
        for assigned_attribute in assigned_attributes:
            instance_to_assignedattributes[
                getattr(assigned_attribute, f"{self.model_name}_id")
            ].append(assigned_attribute)
        return [instance_to_assignedattributes[id] for id in keys]


class AssignedProductAttributesByProductIdLoader(
    BaseAssignedAttributesByInstanceIdLoader
):
    context_key = "assignedproductattributes_by_product"
    assigned_attr_model = AssignedProductAttribute
    model_name = "product"


class AssignedVariantAttributesByProductVariantId(
    BaseAssignedAttributesByInstanceIdLoader
):
    context_key = "assignedvariantattributes_by_productvariant"
    assigned_attr_model = AssignedVariantAttribute
    model_name = "variant"


class AssignedCategoryAttributesByCategoryIdLoader(
    BaseAssignedAttributesByInstanceIdLoader
):
    context_key = "assignedcategoryattributes_by_category"
    assigned_attr_model = AssignedCategoryAttribute
    model_name = "category"


class AssignedCollectionAttributesByCollectionIdLoader(
    BaseAssignedAttributesByInstanceIdLoader
):
    context_key = "assignedcollectionattributes_by_collection"
    assigned_attr_model = AssignedCollectionAttribute
    model_name = "collection"


class AttributeValuesByAssignedAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assignedattribute"
    assigned_attr_model = None

    def batch_load(self, keys):
        attribute_values = self.assigned_attr_model.objects.filter(
            assignment_id__in=keys
        )
        value_ids = [a.value_id for a in attribute_values]

        def map_assignment_to_values(values):
            value_map = dict(zip(value_ids, values))
            assigned_map = defaultdict(list)
            for attribute_value in attribute_values:
                assigned_map[attribute_value.assignment_id].append(
                    value_map.get(attribute_value.value_id)
                )
            return [assigned_map[key] for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(value_ids)
            .then(map_assignment_to_values)
        )


class AttributeValuesByAssignedProductAttributeIdLoader(
    AttributeValuesByAssignedAttributeIdLoader
):
    context_key = "attributevalues_by_assignedproductattribute"
    assigned_attr_model = AssignedProductAttributeValue


class AttributeValuesByAssignedVariantAttributeIdLoader(
    AttributeValuesByAssignedAttributeIdLoader
):
    context_key = "attributevalues_by_assignedvariantattribute"
    assigned_attr_model = AssignedVariantAttributeValue


class AttributeValuesByAssignedCategoryAttributeIdLoader(
    AttributeValuesByAssignedAttributeIdLoader
):
    context_key = "attributevalues_by_assignedcategoryattribute"
    assigned_attr_model = AssignedCategoryAttributeValue


class AttributeValuesByAssignedCollectionAttributeIdLoader(
    AttributeValuesByAssignedAttributeIdLoader
):
    context_key = "attributevalues_by_assignedcollectionattribute"
    assigned_attr_model = AssignedCollectionAttributeValue


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


class SelectedAttributesByCollectionIdLoader(DataLoader):
    context_key = "selectedattributes_by_collection"

    def batch_load(self, keys):
        def with_collections_and_assigned_attributes(collection_attributes):
            assigned_collection_attribute_ids = [
                a.id for attrs in collection_attributes for a in attrs
            ]
            site_settings_id = self.context.site.settings.id
            collection_attributes = dict(zip(keys, collection_attributes))

            def with_attributecollections_and_values(result):
                attribute_collections, attribute_values = result
                attribute_ids = list({ap.attribute_id for ap in attribute_collections})
                attribute_values = dict(
                    zip(assigned_collection_attribute_ids, attribute_values)
                )

                def with_attributes(attributes):
                    id_to_attribute = dict(zip(attribute_ids, attributes))
                    selected_attributes_map = defaultdict(list)
                    assigned_sitesettings_attributes = attribute_collections
                    for key in keys:
                        assigned_collection_attributes = collection_attributes[key]
                        for (
                            assigned_sitesetting_attribute
                        ) in assigned_sitesettings_attributes:
                            collection_assignment = next(
                                (
                                    apa
                                    for apa in assigned_collection_attributes
                                    if apa.assignment_id
                                    == assigned_sitesetting_attribute.id
                                ),
                                None,
                            )
                            attribute = id_to_attribute[
                                assigned_sitesetting_attribute.attribute_id
                            ]
                            if collection_assignment:
                                values = attribute_values[collection_assignment.id]
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

            attribute_collections = AttributeCollectionsBySiteSettingsIdLoader(
                self.context
            ).load(site_settings_id)
            attribute_values = AttributeValuesByAssignedCollectionAttributeIdLoader(
                self.context
            ).load_many(assigned_collection_attribute_ids)
            return Promise.all([attribute_collections, attribute_values]).then(
                with_attributecollections_and_values
            )

        return (
            AssignedCollectionAttributesByCollectionIdLoader(self.context)
            .load_many(keys)
            .then(with_collections_and_assigned_attributes)
        )
