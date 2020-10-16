from graphene import Boolean, relay

from ...page import models
from ..core.connection import CountableDjangoObjectType
from ..translations.fields import TranslationField
from ..translations.types import PageTranslation


class Page(CountableDjangoObjectType):
    translation = TranslationField(PageTranslation, type_name="page")
    is_published = Boolean(required=True, description="Whether the page is published.")

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
            "publication_date",
            "seo_description",
            "seo_title",
            "slug",
            "title",
        ]
        interfaces = [relay.Node]
        model = models.Page

    @staticmethod
    def resolve_is_published(root: models.Page, _info):
        return root.is_visible
