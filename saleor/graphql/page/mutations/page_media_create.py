import graphene
from django.core.exceptions import ValidationError
from django.core.files import File

from ..utils import ALT_CHAR_LIMIT
from ...core import ResolveInfo
from ...core.validators.file import clean_image_file, is_image_url, validate_image_url
from ...plugins.dataloaders import get_plugin_manager_promise

from ....core.http_client import HTTPClient
from ....core.utils.validators import get_oembed_data
from ....page import models, PageMediaTypes
from ....page.error_codes import PageErrorCode
from ....permission.enums import PagePermissions
from ..types import Page, PageMedia
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, Upload, PageError
from ....thumbnail.utils import get_filename_from_url


class PageMediaCreateInput(BaseInputObjectType):
    alt = graphene.String(description="Alt text for a page media.")
    image = Upload(
        required=False, description="Represents an image file in a multipart request."
    )
    page = graphene.ID(
        required=True, description="ID of an page.", name="page"
    )
    media_url = graphene.String(
        required=False, description="Represents an URL to an external media."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAGES


class PageMediaCreate(BaseMutation):
    page = graphene.Field(Page)
    media = graphene.Field(PageMedia)

    class Arguments:
        input = PageMediaCreateInput(
            required=True, description="Fields required to create a page media."
        )

    class Meta:
        description = (
            "Create a media object (image or video URL) associated with page. "
            "For image, this mutation must be sent as a `multipart` request. "
            "More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        doc_category = DOC_CATEGORY_PAGES
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def validate_input(cls, data):
        image = data.get("image")
        media_url = data.get("media_url")
        alt = data.get("alt")

        if not image and not media_url:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Image or external URL is required.",
                        code=PageErrorCode.REQUIRED.value,
                    )
                }
            )
        if image and media_url:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Either image or external URL is required.",
                        code=PageErrorCode.DUPLICATED_INPUT_ITEM.value,
                    )
                }
            )

        if alt and len(alt) > ALT_CHAR_LIMIT:
            raise ValidationError(
                {
                    "input": ValidationError(
                        f"Alt field exceeds the character "
                        f"limit of {ALT_CHAR_LIMIT}.",
                        code=PageErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        cls.validate_input(input)
        page = cls.get_node_or_error(
            info,
            input["page"],
            field="page",
            only_type=Page,
            qs=models.Page.objects.prefetched_for_webhook(),
        )

        alt = input.get("alt", "")
        media_url = input.get("media_url")
        media = None
        if img_data := input.get("image"):
            input["image"] = info.context.FILES.get(img_data)
            image_data = clean_image_file(input, "image", PageErrorCode)
            media = page.media.create(
                image=image_data, alt=alt, type=PageMediaTypes.IMAGE
            )
        if media_url:
            # Remote URLs can point to the images or oembed data.
            # In case of images, file is downloaded. Otherwise we keep only
            # URL to remote media.
            if is_image_url(media_url):
                validate_image_url(
                    media_url, "media_url", PageErrorCode.INVALID.value
                )
                filename = get_filename_from_url(media_url)
                image_data = HTTPClient.send_request(
                    "GET", media_url, stream=True, allow_redirects=False
                )
                image_file = File(image_data.raw, filename)
                media = page.media.create(
                    image=image_file,
                    alt=alt,
                    type=PageMediaTypes.IMAGE,
                )
            else:
                oembed_data, media_type = get_oembed_data(media_url, "media_url")
                media = page.media.create(
                    external_url=oembed_data["url"],
                    alt=oembed_data.get("title", alt),
                    type=media_type,
                    oembed_data=oembed_data,
                )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_updated, page)
        cls.call_event(manager.page_media_created, media)
        return PageMediaCreate(page=page, media=media)
