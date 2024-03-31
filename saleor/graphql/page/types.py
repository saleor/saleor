from typing import Optional

import graphene
from graphene import relay

from .enums import PageMediaType
from .sorters import PageMediaSortingInput
from ..core.utils import from_global_id_or_error
from ...attribute import models as attribute_models
from ...core.utils import build_absolute_uri
from ...page import models
from ...permission.enums import PagePermissions, PageTypePermissions
from ..attribute.filters import AttributeFilterInput, AttributeWhereInput
from ..attribute.types import Attribute, AttributeCountableConnection, SelectedAttribute
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.context import get_database_connection_name
from ..core.descriptions import ADDED_IN_33, DEPRECATED_IN_3X_FIELD, RICH_CONTENT, \
    ADDED_IN_312, ADDED_IN_39
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.federation import federated_entity, resolve_federation_references
from ..core.fields import FilterConnectionField, JSONString, PermissionsField
from ..core.scalars import Date
from ..core.types import ModelObjectType, NonNullList, ThumbnailField
from ..meta.types import ObjectWithMetadata
from ..translations.fields import TranslationField
from ..translations.types import PageTranslation
from ..utils import get_user_or_app_from_context
from .dataloaders import (
    PageAttributesAllByPageTypeIdLoader,
    PageAttributesVisibleInStorefrontByPageTypeIdLoader,
    PagesByPageTypeIdLoader,
    PageTypeByIdLoader,
    SelectedAttributesAllByPageIdLoader,
    SelectedAttributesVisibleInStorefrontPageIdLoader,
    ThumbnailByPageMediaIdSizeAndFormatLoader,
    MediaByPageIdLoader
)
from ...thumbnail.utils import get_thumbnail_format, get_image_or_proxy_url, \
    get_thumbnail_size


@federated_entity("id")
class PageType(ModelObjectType[models.PageType]):
    id = graphene.GlobalID(required=True, description="ID of the page type.")
    name = graphene.String(required=True, description="Name of the page type.")
    slug = graphene.String(required=True, description="Slug of the page type.")
    attributes = NonNullList(
        Attribute, description="Page attributes of that page type."
    )
    available_attributes = FilterConnectionField(
        AttributeCountableConnection,
        filter=AttributeFilterInput(),
        where=AttributeWhereInput(),
        description="Attributes that can be assigned to the page type.",
        permissions=[
            PagePermissions.MANAGE_PAGES,
            PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        ],
    )
    has_pages = PermissionsField(
        graphene.Boolean,
        description="Whether page type has pages assigned.",
        permissions=[
            PagePermissions.MANAGE_PAGES,
            PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        ],
    )

    class Meta:
        description = (
            "Represents a type of page. It defines what attributes are available to "
            "pages of this type."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.PageType

    @staticmethod
    def get_model():
        return models.PageType

    @staticmethod
    def resolve_attributes(root: models.PageType, info: ResolveInfo):
        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            return PageAttributesAllByPageTypeIdLoader(info.context).load(root.pk)
        else:
            return PageAttributesVisibleInStorefrontByPageTypeIdLoader(
                info.context
            ).load(root.pk)
        return PageAttributesAllByPageTypeIdLoader(info.context).load(root.pk)

    @staticmethod
    def resolve_available_attributes(
        root: models.PageType, info: ResolveInfo, **kwargs
    ):
        qs = attribute_models.Attribute.objects.get_unassigned_page_type_attributes(
            root.pk
        ).using(get_database_connection_name(info.context))
        qs = filter_connection_queryset(
            qs, kwargs, info.context, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, AttributeCountableConnection)

    @staticmethod
    def resolve_has_pages(root: models.PageType, info: ResolveInfo):
        return (
            PagesByPageTypeIdLoader(info.context)
            .load(root.pk)
            .then(lambda pages: bool(pages))
        )

    @staticmethod
    def __resolve_references(roots: list["PageType"], info: ResolveInfo):
        database_connection_name = get_database_connection_name(info.context)
        return resolve_federation_references(
            PageType, roots, models.PageType.objects.using(database_connection_name)
        )


class PageTypeCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        node = PageType


class Page(ModelObjectType[models.Page]):
    id = graphene.GlobalID(required=True, description="ID of the page.")
    seo_title = graphene.String(description="Title of the page for SEO.")
    seo_description = graphene.String(description="Description of the page for SEO.")
    title = graphene.String(required=True, description="Title of the page.")
    content = JSONString(description="Content of the page." + RICH_CONTENT)
    publication_date = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `publishedAt` field to fetch the publication date."
        ),
    )
    published_at = graphene.DateTime(
        description="The page publication date." + ADDED_IN_33
    )
    is_published = graphene.Boolean(
        required=True, description="Determines if the page is published."
    )
    slug = graphene.String(required=True, description="Slug of the page.")
    page_type = graphene.Field(
        PageType, required=True, description="Determines the type of page"
    )
    created = graphene.DateTime(
        required=True, description="Date and time at which page was created."
    )
    content_json = JSONString(
        description="Content of the page." + RICH_CONTENT,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `content` field instead.",
        required=True,
    )
    translation = TranslationField(PageTranslation, type_name="page")
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this page.",
    )
    media_by_id = graphene.Field(
        lambda: models.PageMedia,
        id=graphene.Argument(graphene.ID, description="ID of a page media."),
        description="Get a single page media by ID.",
    )
    media = NonNullList(
        lambda: models.PageMedia,
        sort_by=graphene.Argument(
            PageMediaSortingInput, description=f"Sort media. {ADDED_IN_39}"
        ),
        description="List of media for the page.",
    )
    thumbnail = ThumbnailField(description="Thumbnail of the page media.")

    class Meta:
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Page

    @staticmethod
    def resolve_publication_date(root: models.Page, _info: ResolveInfo):
        return root.published_at

    @staticmethod
    def resolve_created(root: models.Page, _info: ResolveInfo):
        return root.created_at

    @staticmethod
    def resolve_page_type(root: models.Page, info: ResolveInfo):
        return PageTypeByIdLoader(info.context).load(root.page_type_id)

    @staticmethod
    def resolve_content_json(root: models.Page, _info: ResolveInfo):
        content = root.content
        return content if content is not None else {}

    @staticmethod
    def resolve_attributes(root: models.Page, info: ResolveInfo):
        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            return SelectedAttributesAllByPageIdLoader(info.context).load(root.id)
        else:
            return SelectedAttributesVisibleInStorefrontPageIdLoader(info.context).load(
                root.id
            )


    @staticmethod
    def resolve_media_by_id(root: models.Page, info, *, id):
        _type, pk = from_global_id_or_error(id, PageMedia)
        return (
            root.media.using(get_database_connection_name(info.context))
            .filter(pk=pk)
            .first()
        )

    @staticmethod
    def resolve_media(root: models.Page, info, sort_by=None):
        if sort_by is None:
            sort_by = {
                "field": ["sort_order"],
                "direction": "",
            }

        def sort_media(media) -> list[PageMedia]:
            reversed = sort_by["direction"] == "-"

            # Nullable first,
            # achieved by adding the number of nonnull fields as firt element of tuple
            def key(x):
                values_tuple = tuple(
                    getattr(x, field)
                    for field in sort_by["field"]
                    if getattr(x, field) is not None
                )
                values_tuple = (len(values_tuple),) + values_tuple
                return values_tuple

            media_sorted = sorted(
                media,
                key=key,
                reverse=reversed,
            )
            return media_sorted
        return MediaByPageIdLoader(info.context).load(root.id).then(sort_media)


class PageMedia(ModelObjectType[models.PageMedia]):
    id = graphene.GlobalID(
        required=True, description="The unique ID of the page media."
    )
    sort_order = graphene.Int(description="The sort order of the media.")
    alt = graphene.String(required=True, description="The alt text of the media.")
    type = PageMediaType(required=True, description="The type of the media.")
    oembed_data = JSONString(required=True, description="The oEmbed data of the media.")
    url = ThumbnailField(
        graphene.String, required=True, description="The URL of the media."
    )
    page_id = graphene.ID(
        description="Page id the media refers to." + ADDED_IN_312
    )

    class Meta:
        description = "Represents a page media."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.PageMedia
        metadata_since = ADDED_IN_312

    @staticmethod
    def resolve_url(
        root: models.PageMedia,
        info,
        *,
        size: Optional[int] = None,
        format: Optional[str] = None,
    ):
        if root.external_url:
            return root.external_url

        if not root.image:
            return

        if size == 0:
            return build_absolute_uri(root.image.url)

        format = get_thumbnail_format(format)
        selected_size = get_thumbnail_size(size)

        def _resolve_url(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, str(root.id), "PageMedia", selected_size, format
            )
            return build_absolute_uri(url)

        return (
            ThumbnailByPageMediaIdSizeAndFormatLoader(info.context)
            .load((root.id, selected_size, format))
            .then(_resolve_url)
        )

    @staticmethod
    def __resolve_references(roots: list["PageMedia"], _info):
        return resolve_federation_references(
            PageMedia, roots, models.PageMedia.objects
        )

    @staticmethod
    def resolve_page_id(root: models.PageMedia, info):
        return graphene.Node.to_global_id("Page", root.page_id)


class PageCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        node = Page
