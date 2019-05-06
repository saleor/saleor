import graphene
from graphene import relay

from ...page import models
from ..core.connection import CountableDjangoObjectType
from ..translations.enums import LanguageCodeEnum
from ..translations.resolvers import resolve_translation
from ..translations.types import PageTranslation


class Page(CountableDjangoObjectType):
    available_on = graphene.Date(
        deprecation_reason=(
            'availableOn is deprecated, use publicationDate instead'))
    is_visible = graphene.Boolean(
        deprecation_reason=(
            'isVisible is deprecated, use isPublished instead'))
    translation = graphene.Field(
        PageTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description='A language code to return the translation for.',
            required=True),
        description=(
            'Returns translated Page fields for the given language code.'),
        resolver=resolve_translation)

    class Meta:
        description = """A static page that can be manually added by a shop
               operator through the dashboard."""
        only_fields = [
            'content', 'content_json', 'created', 'id', 'is_published',
            'publication_date', 'seo_description', 'seo_title', 'slug',
            'title']
        interfaces = [relay.Node]
        model = models.Page

    def resolve_available_on(self, _info):
        return self.publication_date

    def resolve_is_visible(self, _info):
        return self.is_published
