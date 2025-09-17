import graphene

from ...attribute import models as attribute_models
from ...page import models
from ...permission.enums import PagePermissions, PageTypePermissions
from ...permission.utils import all_permissions_required
from ..attribute.dataloaders.assigned_attributes import (
    AttributeByPageIdAndAttributeSlugLoader,
    AttributesByPageIdAndLimitLoader,
    AttributesVisibleToCustomerByPageIdAndLimitLoader,
)
from ..attribute.filters import (
    AttributeFilterInput,
    AttributeWhereInput,
    filter_attribute_search,
)
from ..attribute.types import (
    Attribute,
    AttributeCountableConnection,
    ObjectWithAttributes,
    SelectedAttribute,
)
from ..attribute.utils.shared import AssignedAttributeData
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.const import DEFAULT_NESTED_LIST_LIMIT
from ..core.context import (
    ChannelContext,
    ChannelQsContext,
    get_database_connection_name,
)
from ..core.descriptions import ADDED_IN_322, DEPRECATED_IN_3X_INPUT, RICH_CONTENT
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.federation import federated_entity, resolve_federation_references
from ..core.fields import FilterConnectionField, JSONString, PermissionsField
from ..core.scalars import Date, DateTime, PositiveInt
from ..core.types import ModelObjectType, NonNullList
from ..core.types.context import ChannelContextType
from ..meta.types import ObjectWithMetadata
from ..translations.fields import TranslationField
from ..translations.types import PageTranslation
from .dataloaders import (
    PageAttributesAllByPageTypeIdLoader,
    PageAttributesVisibleInStorefrontByPageTypeIdLoader,
    PagesByPageTypeIdLoader,
    PageTypeByIdLoader,
)


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
        filter=AttributeFilterInput(
            description="Filtering options for attributes. "
            f"{DEPRECATED_IN_3X_INPUT} Use `where` filter instead."
        ),
        where=AttributeWhereInput(
            description="Where filtering options for attributes."
        ),
        search=graphene.String(description="Search attributes."),
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
        def wrap_with_channel_context(attributes):
            return [ChannelContext(attribute, None) for attribute in attributes]

        if all_permissions_required(info.context, [PagePermissions.MANAGE_PAGES]):
            return (
                PageAttributesAllByPageTypeIdLoader(info.context)
                .load(root.pk)
                .then(wrap_with_channel_context)
            )
        return (
            PageAttributesVisibleInStorefrontByPageTypeIdLoader(info.context)
            .load(root.pk)
            .then(wrap_with_channel_context)
        )

    @staticmethod
    def resolve_available_attributes(
        root: models.PageType, info: ResolveInfo, search=None, **kwargs
    ):
        qs = attribute_models.Attribute.objects.get_unassigned_page_type_attributes(
            root.pk
        ).using(get_database_connection_name(info.context))
        qs = filter_connection_queryset(
            qs, kwargs, info.context, allow_replica=info.context.allow_replica
        )
        if search:
            qs = filter_attribute_search(qs, None, search)
        qs = ChannelQsContext(qs=qs, channel_slug=None)
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


class Page(ChannelContextType[models.Page]):
    id = graphene.GlobalID(required=True, description="ID of the page.")
    seo_title = graphene.String(description="Title of the page for SEO.")
    seo_description = graphene.String(description="Description of the page for SEO.")
    title = graphene.String(required=True, description="Title of the page.")
    content = JSONString(description="Content of the page." + RICH_CONTENT)
    publication_date = Date(
        deprecation_reason="Use the `publishedAt` field to fetch the publication date."
    )
    published_at = DateTime(description="The page publication date.")
    is_published = graphene.Boolean(
        required=True, description="Determines if the page is published."
    )
    slug = graphene.String(required=True, description="Slug of the page.")
    page_type = graphene.Field(
        PageType, required=True, description="Determines the type of page"
    )
    created = DateTime(
        required=True, description="Date and time at which page was created."
    )
    content_json = JSONString(
        description="Content of the page." + RICH_CONTENT,
        deprecation_reason="Use the `content` field instead.",
        required=True,
    )
    translation = TranslationField(
        PageTranslation,
        type_name="page",
        resolver=ChannelContextType.resolve_translation,
    )
    attribute = graphene.Field(
        SelectedAttribute,
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description="Get a single attribute attached to page by attribute slug.",
        deprecation_reason="Use `assignedAttribute` field instead.",
    )
    assigned_attribute = graphene.Field(
        "saleor.graphql.attribute.types.AssignedAttribute",
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description="Get a single attribute attached to page by attribute slug."
        + ADDED_IN_322,
    )
    assigned_attributes = NonNullList(
        "saleor.graphql.attribute.types.AssignedAttribute",
        required=True,
        description="List of attributes assigned to this page." + ADDED_IN_322,
        limit=PositiveInt(
            description=(
                "Maximum number of attributes to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this page.",
        deprecation_reason="Use `assignedAttributes` field instead.",
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata, ObjectWithAttributes]
        model = models.Page

    @staticmethod
    def resolve_publication_date(root: ChannelContext[models.Page], _info: ResolveInfo):
        return root.node.published_at

    @staticmethod
    def resolve_created(root: ChannelContext[models.Page], _info: ResolveInfo):
        return root.node.created_at

    @staticmethod
    def resolve_page_type(root: ChannelContext[models.Page], info: ResolveInfo):
        return PageTypeByIdLoader(info.context).load(root.node.page_type_id)

    @staticmethod
    def resolve_content_json(root: ChannelContext[models.Page], _info: ResolveInfo):
        content = root.node.content
        return content if content is not None else {}

    @classmethod
    def resolve_assigned_attributes(
        cls,
        root: ChannelContext[models.Page],
        info: ResolveInfo,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ):
        return cls._resolve_assigned_attributes(root, info, limit)

    @classmethod
    def resolve_assigned_attribute(
        cls, root: ChannelContext[models.Page], info: ResolveInfo, slug: str
    ):
        return cls._resolve_assigned_attribute(root, info, slug)

    @classmethod
    def resolve_attributes(cls, root: ChannelContext[models.Page], info: ResolveInfo):
        return cls._resolve_assigned_attributes(root, info)

    @classmethod
    def _resolve_assigned_attributes(
        cls,
        root: ChannelContext[models.Page],
        info: ResolveInfo,
        limit: int | None = None,
    ):
        page = root.node

        def get_assigned_attributes(
            attributes: list[attribute_models.Attribute],
        ) -> list[AssignedAttributeData]:
            return [
                AssignedAttributeData(
                    attribute=attribute,
                    page_id=page.id,
                    channel_slug=root.channel_slug,
                )
                for attribute in attributes
            ]

        if all_permissions_required(info.context, [PagePermissions.MANAGE_PAGES]):
            dataloader = AttributesByPageIdAndLimitLoader(info.context)
        else:
            dataloader = AttributesVisibleToCustomerByPageIdAndLimitLoader(info.context)
        return dataloader.load((page.id, limit)).then(get_assigned_attributes)

    @classmethod
    def resolve_attribute(
        cls, root: ChannelContext[models.Page], info: ResolveInfo, slug: str
    ):
        return cls._resolve_assigned_attribute(root, info, slug)

    @classmethod
    def _resolve_assigned_attribute(
        cls, root: ChannelContext[models.Page], info: ResolveInfo, slug: str
    ):
        page = root.node

        def with_assigned_attribute(attribute: attribute_models.Attribute | None):
            if not attribute:
                return None
            has_permission = all_permissions_required(
                info.context, [PagePermissions.MANAGE_PAGES]
            )
            if not has_permission and not attribute.visible_in_storefront:
                return None
            return AssignedAttributeData(
                attribute=attribute,
                page_id=page.id,
                channel_slug=root.channel_slug,
            )

        return (
            AttributeByPageIdAndAttributeSlugLoader(info.context)
            .load((page.id, slug))
            .then(with_assigned_attribute)
        )


class PageCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        node = Page
