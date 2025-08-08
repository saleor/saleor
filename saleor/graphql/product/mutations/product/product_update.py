import graphene
from django.core.exceptions import ValidationError

from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from ....attribute.utils.attribute_assignment import AttributeAssignmentMixin
from ....attribute.utils.shared import AttrValuesInput
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.mutations import ModelWithExtRefMutation
from ....core.types.common import ProductError
from ....core.validators import clean_seo_fields
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product
from ..utils import clean_tax_code
from . import product_cleaner as cleaner
from .product_create import ProductInput

T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductUpdate(ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a product to update.")
        external_reference = graphene.String(
            required=False,
            description="External ID of a product to update.",
        )
        input = ProductInput(
            required=True, description="Fields required to update a product."
        )

    class Meta:
        description = "Updates an existing product."
        model = models.Product
        object_type = Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def get_instance(cls, info, **data):
        """Prefetch related fields that are needed to process the mutation."""
        # If we are updating an instance and want to update its attributes,
        # prefetch them.
        object_id = cls.get_object_id(**data)
        if object_id and data.get("attributes"):
            # Prefetches needed by AttributeAssignmentMixin and
            # associate_attribute_values_to_instance
            qs = cls.Meta.model.objects.prefetch_related(
                "product_type__product_attributes__values",
                "product_type__attributeproduct",
            )
            return cls.get_node_or_error(info, object_id, only_type="Product", qs=qs)

        return super().get_instance(info, **data)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        cleaner.clean_description(cleaned_input)
        cleaner.clean_weight(cleaned_input)
        cleaner.clean_slug(cleaned_input, instance)
        cls.clean_attributes(cleaned_input, instance)
        clean_tax_code(cleaned_input)
        clean_seo_fields(cleaned_input)

        return cleaned_input

    @classmethod
    def clean_attributes(cls, cleaned_input, instance):
        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.
        attributes = cleaned_input.get("attributes")
        product_type = instance.product_type
        if attributes and product_type:
            try:
                attributes_qs = product_type.product_attributes.all()
                cleaned_input["attributes"] = AttributeAssignmentMixin.clean_input(
                    attributes, attributes_qs, creation=False
                )
            except ValidationError as e:
                raise ValidationError({"attributes": e}) from e

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
    def save(cls, info: ResolveInfo, instance, cleaned_input, instance_tracker=None):
        with traced_atomic_transaction():
            instance.search_index_dirty = True
            instance.save()
            attributes = cleaned_input.get("attributes")
            if attributes:
                AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def _save_m2m(cls, _info: ResolveInfo, instance, cleaned_data):
        collections = cleaned_data.get("collections", None)
        if collections is not None:
            instance.collections.set(collections)

    @classmethod
    def _post_save_action(cls, info: ResolveInfo, instance):
        product = models.Product.objects.get(pk=instance.pk)
        channel_ids = set(
            product.channel_listings.all().values_list("channel_id", flat=True)
        )
        cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)

        cls.handle_metadata(instance, cleaned_input)

        instance = cls.construct_instance(instance, cleaned_input)

        cls.clean_instance(info, instance)

        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        cls._post_save_action(info, instance)
        return cls.success_response(instance)
