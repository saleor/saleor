import graphene
from django.core.exceptions import ValidationError

from ....product import ProductMediaTypes
from ....product.error_codes import MediaCreateErrorCode
from ....product.media import (
    GRAPHQL_TYPE_TO_OWNER_TYPE,
    OWNER_TYPE_TO_UPDATED_EVENT,
    create_media_from_url,
    probe_media_url,
    validate_media_input,
)
from ....product.tasks import fetch_product_media_image_task
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_324
from ...core.doc_category import DOC_CATEGORY_MEDIA
from ...core.types import BaseInputObjectType, MediaCreateError, Upload
from ...core.utils import WebhookEventInfo
from ...core.validators.file import clean_image_file
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Media
from .base import BaseMediaMutation


class MediaCreateInput(BaseInputObjectType):
    alt = graphene.String(description="Alt text for the media.")
    image = Upload(
        required=False, description="Represents an image file in a multipart request."
    )
    media_url = graphene.String(
        required=False,
        description=(
            "Represents an URL to an external media. The URL is fetched once: if it "
            "points to an image, the image is downloaded in the background; otherwise "
            "it is stored as oEmbed data."
        ),
    )

    class Meta:
        description = "Fields required to create a media object." + ADDED_IN_324
        doc_category = DOC_CATEGORY_MEDIA


class MediaCreate(BaseMediaMutation):
    media = graphene.Field(Media, description="The created media.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description=(
                "ID of the entity the media will be attached to. Supported entities: "
                "`Product`, `Category`, `Collection`, `Page`."
            ),
        )
        input = MediaCreateInput(
            required=True, description="Fields required to create a media object."
        )

    class Meta:
        description = (
            "Create a media object (image or video URL) attached to a product, "
            "category, collection or page. For an image, this mutation must be sent "
            "as a `multipart` request. More detailed specs of the upload format can "
            "be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec\n\n"
            "Requires `MANAGE_PRODUCTS` for product, category and collection owners, "
            "and `MANAGE_PAGES` for page owners." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_MEDIA
        error_type_class = MediaCreateError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MEDIA_CREATED,
                description="A media object was created.",
            ),
        ]

    id_type_to_owner_type = GRAPHQL_TYPE_TO_OWNER_TYPE

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        image = input.get("image")
        media_url = input.get("media_url")
        alt = input.get("alt") or ""

        if error := validate_media_input(image, media_url, alt, MediaCreateErrorCode):
            error_message, error_code, _ = error
            raise ValidationError(
                {"input": ValidationError(error_message, code=error_code)}
            )

        owner_type, owner = cls.get_owner(id, MediaCreateErrorCode)

        if image:
            input["image"] = info.context.FILES.get(image)
            image_data = clean_image_file(input, "image", MediaCreateErrorCode)
            media = owner.media.create(
                image=image_data, alt=alt, type=ProductMediaTypes.IMAGE
            )
        else:
            # Remote URLs can point to images or to oEmbed data. Images are fetched
            # asynchronously by a task; for anything else only the URL is kept.
            probe_result = probe_media_url(media_url, MediaCreateErrorCode)
            media = create_media_from_url(owner, media_url, alt, probe_result)
            if probe_result.is_image:
                fetch_product_media_image_task.delay(media.pk)

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(getattr(manager, OWNER_TYPE_TO_UPDATED_EVENT[owner_type]), owner)
        cls.call_event(manager.media_created, media)
        return MediaCreate(media=media)
