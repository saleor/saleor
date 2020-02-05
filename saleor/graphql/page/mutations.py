import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import PagePermissions
from ...page import models
from ...page.error_codes import PageErrorCode
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import PageError, SeoInput
from ..core.utils import clean_seo_fields, validate_slug_and_generate_if_needed


class PageInput(graphene.InputObjectType):
    slug = graphene.String(description="Page internal name.")
    title = graphene.String(description="Page title.")
    content = graphene.String(
        description=("Page content. May consist of ordinary text, HTML and images.")
    )
    content_json = graphene.JSONString(description="Page content in JSON format.")
    is_published = graphene.Boolean(
        description="Determines if page is visible in the storefront."
    )
    publication_date = graphene.String(
        description="Publication date. ISO 8601 standard."
    )
    seo = SeoInput(description="Search engine optimization fields.")


class PageCreate(ModelMutation):
    class Arguments:
        input = PageInput(
            required=True, description="Fields required to create a page."
        )

    class Meta:
        description = "Creates a new page."
        model = models.Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "title", cleaned_input
            )
        except ValidationError as error:
            error.code = PageErrorCode.REQUIRED
            raise ValidationError({"slug": error})
        clean_seo_fields(cleaned_input)
        return cleaned_input


class PageUpdate(PageCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to update.")
        input = PageInput(
            required=True, description="Fields required to update a page."
        )

    class Meta:
        description = "Updates an existing page."
        model = models.Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"


class PageDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to delete.")

    class Meta:
        description = "Deletes a page."
        model = models.Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"
