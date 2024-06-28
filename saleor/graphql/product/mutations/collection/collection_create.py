import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError

from .....core.utils.date_time import convert_to_utc_date_time
from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import CollectionErrorCode
from .....product.tasks import collection_product_updated_task
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_38, DEPRECATED_IN_3X_INPUT, RICH_CONTENT
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.fields import JSONString
from ....core.mutations import ModelMutation
from ....core.scalars import Date
from ....core.types import (
    BaseInputObjectType,
    CollectionError,
    NonNullList,
    SeoInput,
    Upload,
)
from ....core.validators import clean_seo_fields, validate_slug_and_generate_if_needed
from ....core.validators.file import clean_image_file
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Collection

# Batch size of 25k ids, assuming their pks are at least 7 digits each
# after json serialization, weights 225kB of payload.
PRODUCTS_BATCH_SIZE = 25000


class CollectionInput(BaseInputObjectType):
    is_published = graphene.Boolean(
        description="Informs whether a collection is published."
    )
    name = graphene.String(description="Name of the collection.")
    slug = graphene.String(description="Slug of the collection.")
    description = JSONString(
        description="Description of the collection." + RICH_CONTENT
    )
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for an image.")
    seo = SeoInput(description="Search engine optimization fields.")
    publication_date = Date(
        description=(f"Publication date. ISO 8601 standard. {DEPRECATED_IN_3X_INPUT}")
    )
    metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the collection metadata." + ADDED_IN_38
        ),
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the collection private metadata." + ADDED_IN_38
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class CollectionCreateInput(CollectionInput):
    products = NonNullList(
        graphene.ID,
        description="List of products to be added to the collection.",
        name="products",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class CollectionCreate(ModelMutation):
    class Arguments:
        input = CollectionCreateInput(
            required=True, description="Fields required to create a collection."
        )

    class Meta:
        description = "Creates a new collection."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = CollectionErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})
        if data.get("background_image"):
            clean_image_file(cleaned_input, "background_image", CollectionErrorCode)
        is_published = cleaned_input.get("is_published")
        publication_date = cleaned_input.get("publication_date")
        if is_published and not publication_date:
            cleaned_input["published_at"] = datetime.datetime.now(pytz.UTC)
        elif publication_date:
            cleaned_input["published_at"] = convert_to_utc_date_time(publication_date)
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @staticmethod
    def batch_product_ids(ids):
        _length = len(ids)
        for i in range(0, _length, PRODUCTS_BATCH_SIZE):
            yield ids[i : i + PRODUCTS_BATCH_SIZE]

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.collection_created, instance)

        product_ids = list(instance.products.values_list("id", flat=True))
        for ids_batch in cls.batch_product_ids(product_ids):
            collection_product_updated_task.delay(ids_batch)

        if product_ids:
            channel_ids = models.ProductChannelListing.objects.filter(
                product_id__in=product_ids
            ).values_list("channel_id", flat=True)
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **kwargs):
        result = super().perform_mutation(_root, info, **kwargs)
        return CollectionCreate(
            collection=ChannelContext(node=result.collection, channel_slug=None)
        )
