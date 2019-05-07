import graphene
from django.utils.text import slugify

from ...page import models
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import SeoInput
from ..core.utils import clean_seo_fields


class PageInput(graphene.InputObjectType):
    slug = graphene.String(description='Page internal name.')
    title = graphene.String(description='Page title.')
    content = graphene.String(
        description=(
            'Page content. May consists of ordinary text, HTML and images.'))
    content_json = graphene.JSONString(
        description='Page content in JSON format.')
    is_published = graphene.Boolean(
        description='Determines if page is visible in the storefront')
    publication_date = graphene.String(
        description='Publication date. ISO 8601 standard.')
    seo = SeoInput(description='Search engine optimization fields.')


class PageCreate(ModelMutation):
    class Arguments:
        input = PageInput(
            required=True, description='Fields required to create a page.')

    class Meta:
        description = 'Creates a new page.'
        model = models.Page
        permissions = ('page.manage_pages', )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        slug = cleaned_input.get('slug', '')
        if not slug:
            cleaned_input['slug'] = slugify(cleaned_input['title'])
        clean_seo_fields(cleaned_input)
        return cleaned_input


class PageUpdate(PageCreate):
    class Arguments:
        id = graphene.ID(required=True, description='ID of a page to update.')
        input = PageInput(
            required=True, description='Fields required to update a page.')

    class Meta:
        description = 'Updates an existing page.'
        model = models.Page


class PageDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description='ID of a page to delete.')

    class Meta:
        description = 'Deletes a page.'
        model = models.Page
        permissions = ('page.manage_pages', )
