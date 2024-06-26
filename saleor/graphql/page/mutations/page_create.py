from datetime import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....page import models
from ....page.error_codes import PageErrorCode
from ....permission.enums import PagePermissions
from ...attribute.types import AttributeValueInput
from ...attribute.utils import PageAttributeAssignmentMixin
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_33, DEPRECATED_IN_3X_INPUT, RICH_CONTENT
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.fields import JSONString
from ...core.mutations import ModelMutation
from ...core.scalars import DateTime
from ...core.types import BaseInputObjectType, NonNullList, PageError, SeoInput
from ...core.validators import clean_seo_fields, validate_slug_and_generate_if_needed
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Page


class PageInput(BaseInputObjectType):
    slug = graphene.String(description="Page internal name.")
    title = graphene.String(description="Page title.")
    content = JSONString(description="Page content." + RICH_CONTENT)
    attributes = NonNullList(AttributeValueInput, description="List of attributes.")
    is_published = graphene.Boolean(
        description="Determines if page is visible in the storefront."
    )
    publication_date = graphene.String(
        description=(
            f"Publication date. ISO 8601 standard. {DEPRECATED_IN_3X_INPUT} "
            "Use `publishedAt` field instead."
        )
    )
    published_at = DateTime(
        description="Publication date time. ISO 8601 standard." + ADDED_IN_33
    )
    seo = SeoInput(description="Search engine optimization fields.")

    class Meta:
        doc_category = DOC_CATEGORY_PAGES


class PageCreateInput(PageInput):
    page_type = graphene.ID(
        description="ID of the page type that page belongs to.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAGES


class PageCreate(ModelMutation):
    class Arguments:
        input = PageCreateInput(
            required=True, description="Fields required to create a page."
        )

    class Meta:
        description = "Creates a new page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_attributes(cls, attributes: dict, page_type: models.PageType):
        attributes_qs = page_type.page_attributes.prefetch_related("values")
        cleaned_attributes = PageAttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, is_page_attributes=True
        )
        return cleaned_attributes

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "title", cleaned_input
            )
        except ValidationError as error:
            error.code = PageErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        if "publication_date" in cleaned_input and "published_at" in cleaned_input:
            raise ValidationError(
                {
                    "publication_date": ValidationError(
                        "Only one of argument: publicationDate or publishedAt "
                        "must be specified.",
                        code=PageErrorCode.INVALID.value,
                    )
                }
            )

        is_published = cleaned_input.get("is_published")
        publication_date = cleaned_input.get("published_at") or cleaned_input.get(
            "publication_date"
        )
        if is_published and not publication_date:
            cleaned_input["published_at"] = datetime.now(pytz.UTC)
        elif "publication_date" in cleaned_input or "published_at" in cleaned_input:
            cleaned_input["published_at"] = publication_date

        attributes = cleaned_input.get("attributes")
        page_type = (
            instance.page_type if instance.pk else cleaned_input.get("page_type")
        )
        if attributes and page_type:
            try:
                cleaned_input["attributes"] = cls.clean_attributes(
                    attributes, page_type
                )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})

        clean_seo_fields(cleaned_input)

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)

            attributes = cleaned_data.get("attributes")
            if attributes:
                PageAttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_created, instance)
