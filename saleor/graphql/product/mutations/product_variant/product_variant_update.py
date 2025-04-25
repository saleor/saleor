from typing import cast

import graphene
from django.core.exceptions import ValidationError

from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....core.utils.update_mutation_manager import InstanceTracker
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.utils.variants import generate_and_set_variant_name
from ....attribute.utils import (
    AttributeAssignmentMixin,
    AttrValuesInput,
    has_input_modified_attribute_values,
)
from ....core import ResolveInfo
from ....core.mutations import ModelWithExtRefMutation
from ....core.types import ProductError
from ....core.utils import ext_ref_to_global_id_or_error
from ....core.validators import validate_one_of_args_is_in_mutation
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import ProductVariant
from .product_variant_create import ProductVariantCreate, ProductVariantInput

T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductVariantUpdate(ProductVariantCreate, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a product to update.")
        external_reference = graphene.String(
            required=False,
            description="External ID of a product variant to update.",
        )
        sku = graphene.String(
            required=False,
            description="SKU of a product variant to update.",
        )
        input = ProductVariantInput(
            required=True, description="Fields required to update a product variant."
        )

    class Meta:
        description = "Updates an existing variant for product."
        model = models.ProductVariant
        object_type = ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        errors_mapping = {"price_amount": "price"}
        support_meta_field = True
        support_private_meta_field = True

    FIELDS_TO_TRACK = [
        "external_reference",
        "is_preorder",
        "metadata",
        "name",
        "preorder_end_date",
        "preorder_global_threshold",
        "private_metadata",
        "quantity_limit_per_customer",
        "sku",
        "track_inventory",
        "weight",
    ]

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes_data, used_attribute_values, instance=None
    ):
        if not has_input_modified_attribute_values(instance, attributes_data):
            return
        # if assigned attributes is getting updated run duplicated attribute validation
        super().validate_duplicated_attribute_values(
            attributes_data, used_attribute_values
        )

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data) -> models.ProductVariant | None:
        """Prefetch related fields that are needed to process the mutation.

        If we are updating an instance and want to update its attributes, prefetch them.
        """
        object_id = data.get("id")
        object_sku = data.get("sku")
        ext_ref = data.get("external_reference")
        attributes = data.get("attributes")

        if attributes:
            # Prefetches needed by AttributeAssignmentMixin and
            # associate_attribute_values_to_instance
            qs = models.ProductVariant.objects.prefetch_related(
                "product__product_type__variant_attributes__values",
                "product__product_type__attributevariant",
            )
        else:
            # Use the default queryset.
            qs = models.ProductVariant.objects.all()

        if ext_ref:
            object_id = ext_ref_to_global_id_or_error(models.ProductVariant, ext_ref)

        if object_id:
            return cls.get_node_or_error(
                info, object_id, only_type=ProductVariant, qs=qs
            )
        if object_sku:
            instance = qs.filter(sku=object_sku).first()
            if not instance:
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            f"Couldn't resolve to a node: {object_sku}",
                            code="not_found",
                        )
                    }
                )
            return instance
        return None

    @classmethod
    def get_product(cls, cleaned_input: dict, instance) -> models.Product:
        return instance.product

    @classmethod
    def set_track_inventory(cls, _info, instance, cleaned_input):
        track_inventory = cleaned_input.get("track_inventory")
        if track_inventory is not None:
            instance.track_inventory = track_inventory

    @classmethod
    def _save_variant_instance(cls, instance, modified_instance_fields):
        update_fields = ["updated_at"] + modified_instance_fields
        instance.save(update_fields=update_fields)

    @classmethod
    def _save(
        cls, info: ResolveInfo, instance_tracker: InstanceTracker, cleaned_input
    ) -> tuple[bool, bool, bool]:
        instance = instance_tracker.instance
        modified_instance_fields = instance_tracker.get_modified_fields()
        metadata_changed = (
            "metadata" in modified_instance_fields
            or "private_metadata" in modified_instance_fields
        )
        attribute_changed = False
        if attributes_data := cleaned_input.get("attributes"):
            attribute_changed = has_input_modified_attribute_values(
                instance, attributes_data
            )

        refresh_product_search_index = False
        with traced_atomic_transaction():
            # handle product variant
            if modified_instance_fields:
                cls._save_variant_instance(instance, modified_instance_fields)
                if (
                    "sku" in modified_instance_fields
                    or "name" in modified_instance_fields
                ):
                    refresh_product_search_index = True

            # handle attributes
            if attribute_changed:
                AttributeAssignmentMixin.save(instance, attributes_data)
                refresh_product_search_index = True

            # handle product
            if refresh_product_search_index:
                instance.product.search_index_dirty = True
                product_update_fields = ["updated_at", "search_index_dirty"]
            else:
                product_update_fields = []
            if not instance.product.default_variant:
                instance.product.default_variant = instance
                product_update_fields.append("default_variant")
            if product_update_fields:
                instance.product.save(update_fields=product_update_fields)

            return bool(modified_instance_fields), attribute_changed, metadata_changed

    @classmethod
    def construct_instance(cls, instance, cleaned_input) -> models.ProductVariant:
        instance = super().construct_instance(instance, cleaned_input)
        cls.set_track_inventory(None, instance, cleaned_input)
        if not instance.name:
            generate_and_set_variant_name(instance, cleaned_input.get("sku"))
        return instance

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        root,
        info: ResolveInfo,
        /,
        *,
        external_reference=None,
        id=None,
        sku=None,
        input,
    ):
        validate_one_of_args_is_in_mutation(
            "sku",
            sku,
            "id",
            id,
            "external_reference",
            external_reference,
        )
        instance = cls.get_instance(
            info, id=id, sku=sku, external_reference=external_reference, input=input
        )
        instance = cast(models.ProductVariant, instance)
        instance_tracker = InstanceTracker(instance, cls.FIELDS_TO_TRACK)

        cleaned_input = cls.clean_input(info, instance, input)

        metadata_list: list[MetadataInput] = cleaned_input.pop("metadata", None)
        private_metadata_list: list[MetadataInput] = cleaned_input.pop(
            "private_metadata", None
        )
        metadata_collection = cls.create_metadata_from_graphql_input(
            metadata_list, error_field_name="metadata"
        )
        private_metadata_collection = cls.create_metadata_from_graphql_input(
            private_metadata_list, error_field_name="private_metadata"
        )

        cls.construct_instance(instance, cleaned_input)
        cls.validate_and_update_metadata(
            instance, metadata_collection, private_metadata_collection
        )
        cls.clean_instance(info, instance)

        variant_modified, attribute_modified, metadata_modified = cls._save(
            info, instance_tracker, cleaned_input
        )
        cls._save_m2m(info, instance, cleaned_input)
        cls._post_save_action(
            info,
            instance,
            cleaned_input,
            variant_modified,
            attribute_modified,
            metadata_modified,
        )

        return cls.success_response(instance)

    @classmethod
    def _post_save_action(
        cls,
        info: ResolveInfo,
        instance,
        cleaned_input,
        variant_modified: bool,
        attribute_modified: bool,
        metadata_modified: bool,
    ):
        if variant_modified or attribute_modified or metadata_modified:
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(manager.product_variant_updated, instance)

            if metadata_modified:
                cls.call_event(manager.product_variant_metadata_updated, instance)

            super().post_save_action(info, instance, cleaned_input)
