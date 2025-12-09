from typing import cast

import graphene
from django.core.exceptions import ValidationError

from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....core.utils.update_mutation_manager import InstanceTracker
from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from .....product.utils.variants import generate_and_set_variant_name
from ....attribute.utils.attribute_assignment import (
    AttributeAssignmentMixin,
)
from ....attribute.utils.shared import (
    AttrValuesInput,
    has_input_modified_attribute_values,
)
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.mutations import DeprecatedModelMutation
from ....core.types import ProductError
from ....core.utils import ext_ref_to_global_id_or_error
from ....core.validators import validate_one_of_args_is_in_mutation
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise
from ...types import ProductVariant
from ...utils import clean_variant_sku
from ..utils import PRODUCT_VARIANT_UPDATE_FIELDS
from . import product_variant_cleaner as cleaner
from .product_variant_create import ProductVariantInput

T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductVariantUpdate(DeprecatedModelMutation):
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

    FIELDS_TO_TRACK = list(PRODUCT_VARIANT_UPDATE_FIELDS)

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
    def clean_input(
        cls,
        info: ResolveInfo,
        instance: models.ProductVariant,
        data: dict,
        **kwargs,
    ):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        cleaner.clean_weight(cleaned_input)
        cleaner.clean_quantity_limit(cleaned_input)
        cls.clean_attributes(cleaned_input, instance)
        if "sku" in cleaned_input:
            cleaned_input["sku"] = clean_variant_sku(cleaned_input.get("sku"))
        cleaner.clean_preorder_settings(cleaned_input)

        return cleaned_input

    @classmethod
    def clean_attributes(cls, cleaned_input: dict, instance: models.ProductVariant):
        product = instance.product
        product_type = product.product_type

        variant_attributes_ids = set()
        variant_attributes_external_refs = set()
        for attr_id, external_ref in product_type.variant_attributes.values_list(
            "id", "external_reference"
        ):
            if external_ref:
                variant_attributes_external_refs.add(external_ref)
            variant_attributes_ids.add(graphene.Node.to_global_id("Attribute", attr_id))

        attributes = cleaned_input.get("attributes") or []
        attributes_ids = {attr["id"] for attr in attributes if attr.get("id") or []}
        attrs_external_refs = {
            attr["external_reference"]
            for attr in attributes
            if attr.get("external_reference") or []
        }
        invalid_attributes = attributes_ids - variant_attributes_ids
        invalid_attributes |= attrs_external_refs - variant_attributes_external_refs
        if len(invalid_attributes) > 0:
            raise ValidationError(
                "Given attributes are not a variant attributes.",
                code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.value,
                params={"attributes": invalid_attributes},
            )

        # Run the validation only if product type is configurable
        if product_type.has_variants:
            # Attributes are provided as list of `AttributeValueInput` objects.
            # We need to transform them into the format they're stored in the
            # `Product` model, which is HStore field that maps attribute's PK to
            # the value's PK.
            try:
                if attributes:
                    attributes_qs = product_type.variant_attributes.all()
                    cleaned_attributes: T_INPUT_MAP = (
                        AttributeAssignmentMixin.clean_input(
                            attributes, attributes_qs, creation=False
                        )
                    )
                    cleaned_input["attributes"] = cleaned_attributes

            except ValidationError as e:
                raise ValidationError({"attributes": e}) from e
        else:
            if attributes:
                raise ValidationError(
                    "Cannot assign attributes for product type without variants",
                    ProductErrorCode.INVALID.value,
                )

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
        cls,
        instance_tracker: InstanceTracker,
        cleaned_input,
    ) -> tuple[bool, bool, bool]:
        instance = cast(models.ProductVariant, instance_tracker.instance)
        modified_instance_fields = instance_tracker.get_modified_fields()
        metadata_modified = (
            "metadata" in modified_instance_fields
            or "private_metadata" in modified_instance_fields
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
            attribute_modified = cls._save_attributes(instance, cleaned_input)
            if attribute_modified:
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

            # variant modified if any field except metadata changed
            variant_modified = bool(
                set(modified_instance_fields) - {"metadata", "private_metadata"}
            )
            return variant_modified, metadata_modified, attribute_modified

    @classmethod
    def _save_attributes(cls, instance, cleaned_input) -> bool:
        attribute_modified = False
        if attributes_data := cleaned_input.get("attributes"):
            try:
                pre_save_bulk = AttributeAssignmentMixin.pre_save_values(
                    instance, attributes_data
                )
                if attribute_modified := has_input_modified_attribute_values(
                    instance,
                    pre_save_bulk,
                ):
                    AttributeAssignmentMixin.save(
                        instance,
                        attributes_data,
                        pre_save_bulk,
                    )
            except ValidationError as e:
                raise ValidationError({"attributes": e}) from e
        return attribute_modified

    @classmethod
    def construct_instance(cls, instance, cleaned_input) -> models.ProductVariant:
        instance = super().construct_instance(instance, cleaned_input)
        cls.set_track_inventory(None, instance, cleaned_input)
        if not instance.name:
            generate_and_set_variant_name(instance, cleaned_input.get("sku"))
        return instance

    @classmethod
    def _post_save_action(
        cls,
        info: ResolveInfo,
        instance,
        variant_modified: bool,
        attribute_modified: bool,
        metadata_modified: bool,
        use_legacy_webhooks_emission: bool,
    ):
        manager = get_plugin_manager_promise(info.context).get()
        if (
            # if any variant related field has been changed
            variant_modified
            or attribute_modified
            # if any metadata has been changed and legacy emission is enabled
            or (metadata_modified and use_legacy_webhooks_emission)
        ):
            cls.call_event(manager.product_variant_updated, instance)

            channel_ids = models.ProductChannelListing.objects.filter(
                product_id=instance.product_id
            ).values_list("channel_id", flat=True)
            # This will recalculate discounted prices for products.
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

        if metadata_modified:
            cls.call_event(manager.product_variant_metadata_updated, instance)

    @classmethod
    def handle_metadata(cls, instance, cleaned_input):
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
        cls.validate_and_update_metadata(
            instance, metadata_collection, private_metadata_collection
        )

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

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

        cls.handle_metadata(instance, cleaned_input)

        cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        site = get_site_promise(info.context).get()
        use_legacy_webhooks_emission = site.settings.use_legacy_update_webhook_emission
        variant_modified, metadata_modified, attribute_modified = cls._save(
            instance_tracker, cleaned_input
        )
        cls._save_m2m(info, instance, cleaned_input)
        cls._post_save_action(
            info,
            instance,
            variant_modified,
            attribute_modified,
            metadata_modified,
            use_legacy_webhooks_emission,
        )

        return cls.success_response(instance)
