from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils.text import slugify

from .....attribute import AttributeInputType
from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.models import ProductChannelListing
from .....product.utils.variants import generate_and_set_variant_name
from ....attribute.utils import AttributeAssignmentMixin, AttrValuesInput
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_38, ADDED_IN_310
from ....core.mutations import ModelWithExtRefMutation
from ....core.types import ProductError
from ....core.utils import ext_ref_to_global_id_or_error
from ....core.validators import validate_one_of_args_is_in_mutation
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import ProductVariant
from ...utils import get_used_attribute_values_for_variant
from .product_variant_create import ProductVariantCreate, ProductVariantInput

T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductVariantUpdate(ProductVariantCreate, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a product to update.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a product variant to update. {ADDED_IN_310}",
        )
        sku = graphene.String(
            required=False,
            description="SKU of a product variant to update." + ADDED_IN_38,
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

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.variant_attributes.all()
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False
        )
        return attributes

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes_data, used_attribute_values, instance=None
    ):
        # Check if the variant is getting updated,
        # and the assigned attributes do not change
        if instance.product_id is not None:
            assigned_attributes = get_used_attribute_values_for_variant(instance)
            input_attribute_values = defaultdict(list)
            for attr, attr_data in attributes_data:
                if attr.input_type == AttributeInputType.FILE:
                    values = (
                        [slugify(attr_data.file_url.split("/")[-1])]
                        if attr_data.file_url
                        else []
                    )
                else:
                    values = attr_data.values
                input_attribute_values[attr_data.global_id].extend(values)
            if input_attribute_values == assigned_attributes:
                return
        # if assigned attributes is getting updated run duplicated attribute validation
        super().validate_duplicated_attribute_values(
            attributes_data, used_attribute_values
        )

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
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
            qs = cls.Meta.model.objects.prefetch_related(
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
                info, object_id, only_type="ProductVariant", qs=qs
            )
        elif object_sku:
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

    @classmethod
    def set_track_inventory(cls, _info, instance, cleaned_input):
        track_inventory = cleaned_input.get("track_inventory")
        if track_inventory is not None:
            instance.track_inventory = track_inventory

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        super().post_save_action(info, instance, cleaned_input)
        channel_ids = ProductChannelListing.objects.filter(
            product_id=instance.product_id
        ).values_list("channel_id", flat=True)
        cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

    @classmethod
    def _save(cls, info: ResolveInfo, instance, cleaned_input, base_fields_changed):
        new_variant = instance.pk is None
        variant_modified = False
        product_search_index_marked_dirty = False
        with traced_atomic_transaction():
            if base_fields_changed:
                instance.save()
                variant_modified = True
            if not instance.product.default_variant:
                instance.product.default_variant = instance
                instance.product.search_index_dirty = True
                instance.product.save(
                    update_fields=[
                        "default_variant",
                        "updated_at",
                        "search_index_dirty",
                    ]
                )
                product_search_index_marked_dirty = True
            if stocks := cleaned_input.get("stocks"):
                cls.create_variant_stocks(instance, stocks)
                variant_modified = True
            if attributes := cleaned_input.get("attributes"):
                AttributeAssignmentMixin.save(instance, attributes)
                variant_modified = True

            if variant_modified:
                if not product_search_index_marked_dirty:
                    instance.product.search_index_dirty = True
                    instance.product.save(update_fields=["search_index_dirty"])
                manager = get_plugin_manager_promise(info.context).get()
                event_to_call = (
                    manager.product_variant_created
                    if new_variant
                    else manager.product_variant_updated
                )
                cls.call_event(event_to_call, instance)

    @classmethod
    def construct_instance(cls, instance, cleaned_input):
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
        old_instance_data = model_to_dict(instance).copy()

        cleaned_input = cls.clean_input(info, instance, input)
        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)
        instance = cls.construct_instance(instance, cleaned_input)

        cls.validate_and_update_metadata(instance, metadata_list, private_metadata_list)
        cls.clean_instance(info, instance)

        base_fields_changed = old_instance_data != model_to_dict(instance)
        cls._save(info, instance, cleaned_input, base_fields_changed)
        cls._save_m2m(info, instance, cleaned_input)
        # add to cleaned_input popped metadata to allow running post save events
        # that depends on the metadata inputs
        if metadata_list:
            cleaned_input["metadata"] = metadata_list
        if private_metadata_list:
            cleaned_input["private_metadata"] = private_metadata_list

        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)
