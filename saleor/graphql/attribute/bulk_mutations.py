import graphene
from django.db.models import Exists, OuterRef, Q

from ...attribute import models
from ...core.permissions import PageTypePermissions
from ...product import models as product_models
from ...product.search import update_products_search_vector
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types import AttributeError, NonNullList
from ..utils import resolve_global_ids_to_primary_keys
from .types import Attribute, AttributeValue


class AttributeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of attribute IDs to delete."
        )

    class Meta:
        description = "Deletes attributes."
        model = models.Attribute
        object_type = Attribute
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def perform_mutation(cls, root, info, ids, **data):
        if not ids:
            return 0, {}
        _, attribute_pks = resolve_global_ids_to_primary_keys(ids, "Attribute")
        product_ids = cls.get_product_ids_to_update(attribute_pks)
        response = super().perform_mutation(root, info, ids, **data)
        update_products_search_vector(
            product_models.Product.objects.filter(id__in=product_ids)
        )
        return response

    @classmethod
    def get_product_ids_to_update(cls, attribute_pks):
        attribute_product = models.AttributeProduct.objects.filter(
            attribute_id__in=attribute_pks
        )
        assigned_product_attrs = models.AssignedProductAttribute.objects.filter(
            Exists(attribute_product.filter(id=OuterRef("assignment_id")))
        )

        attribute_variant = models.AttributeVariant.objects.filter(
            attribute_id__in=attribute_pks
        )
        assigned_variant_attrs = models.AssignedVariantAttribute.objects.filter(
            Exists(attribute_variant.filter(id=OuterRef("assignment_id")))
        )
        variants = product_models.ProductVariant.objects.filter(
            Exists(assigned_variant_attrs.filter(variant_id=OuterRef("id")))
        )

        product_ids = product_models.Product.objects.filter(
            Exists(assigned_product_attrs.filter(product_id=OuterRef("id")))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).values_list("id", flat=True)
        return list(product_ids)

    @classmethod
    def bulk_action(cls, info, queryset):
        attributes = list(queryset)
        queryset.delete()
        for attribute in attributes:
            info.context.plugins.attribute_deleted(attribute)


class AttributeValueBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of attribute value IDs to delete.",
        )

    class Meta:
        description = "Deletes values of attributes."
        model = models.AttributeValue
        object_type = AttributeValue
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def perform_mutation(cls, root, info, ids, **data):
        if not ids:
            return 0, {}
        _, attribute_pks = resolve_global_ids_to_primary_keys(ids, "AttributeValue")
        product_ids = cls.get_product_ids_to_update(attribute_pks)
        response = super().perform_mutation(root, info, ids, **data)
        update_products_search_vector(
            product_models.Product.objects.filter(id__in=product_ids)
        )
        return response

    @classmethod
    def bulk_action(cls, info, queryset):
        attributes = {value.attribute for value in queryset}
        values = list(queryset)
        queryset.delete()
        for value in values:
            info.context.plugins.attribute_value_deleted(value)
        for attribute in attributes:
            info.context.plugins.attribute_updated(attribute)

    @classmethod
    def get_product_ids_to_update(cls, value_pks):
        assigned_product_values = models.AssignedProductAttributeValue.objects.filter(
            value_id__in=value_pks
        )
        assigned_product_attrs = models.AssignedProductAttribute.objects.filter(
            Exists(assigned_product_values.filter(assignment_id=OuterRef("id")))
        )

        assigned_variant_values = models.AssignedVariantAttributeValue.objects.filter(
            value_id__in=value_pks
        )
        assigned_variant_attrs = models.AssignedVariantAttribute.objects.filter(
            Exists(assigned_variant_values.filter(assignment_id=OuterRef("id")))
        )
        variants = product_models.ProductVariant.objects.filter(
            Exists(Exists(assigned_variant_attrs.filter(variant_id=OuterRef("id"))))
        )

        product_ids = product_models.Product.objects.filter(
            Exists(assigned_product_attrs.filter(product_id=OuterRef("id")))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).values_list("id", flat=True)
        return list(product_ids)
