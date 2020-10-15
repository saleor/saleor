import graphene
from graphene import relay
from graphene_federation import key

from ...core.permissions import PagePermissions
from ...page import models
from ...product import models as product_models
from ..core.connection import CountableDjangoObjectType
from ..core.fields import FilterInputConnectionField
from ..decorators import permission_required
from ..meta.types import ObjectWithMetadata
from ..product.dataloaders.attributes import PageAttributesByPageTypeIdLoader
from ..product.filters import AttributeFilterInput
from ..product.types import Attribute
from ..translations.fields import TranslationField
from ..translations.types import PageTranslation


class Page(CountableDjangoObjectType):
    translation = TranslationField(PageTranslation, type_name="page")

    class Meta:
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        only_fields = [
            "content",
            "content_json",
            "created",
            "id",
            "is_published",
            "publication_date",
            "seo_description",
            "seo_title",
            "slug",
            "title",
        ]
        interfaces = [relay.Node]
        model = models.Page


@key(fields="id")
class PageType(CountableDjangoObjectType):
    attributes = graphene.List(
        Attribute, description="Page type attribute of that page type."
    )
    available_attributes = FilterInputConnectionField(
        Attribute, filter=AttributeFilterInput()
    )

    class Meta:
        description = (
            "Represents a type of page. It defines what attributes are available to "
            "pages of this type."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.PageType
        only_fields = ["id", "name", "slug"]

    @staticmethod
    def resolve_attributes(root: models.PageType, info):
        return PageAttributesByPageTypeIdLoader(info.context).load(root.pk)

    @staticmethod
    @permission_required(PagePermissions.MANAGE_PAGES)
    def resolve_available_attributes(root: models.PageType, info, **kwargs):
        return product_models.Attribute.objects.get_unassigned_page_type_attributes(
            root.pk
        )
