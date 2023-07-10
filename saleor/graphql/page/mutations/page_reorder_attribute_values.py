import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....page import models as page_models
from ....page.error_codes import PageErrorCode
from ....permission.enums import PagePermissions
from ...attribute.mutations import BaseReorderAttributeValuesMutation
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.inputs import ReorderInput
from ...core.types import NonNullList, PageError
from ...page.types import Page


class PageReorderAttributeValues(BaseReorderAttributeValuesMutation):
    page = graphene.Field(
        Page, description="Page from which attribute values are reordered."
    )

    class Meta:
        description = "Reorder page attribute values."
        doc_category = DOC_CATEGORY_PAGES
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    class Arguments:
        page_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a page."
        )
        attribute_id = graphene.Argument(
            graphene.ID, required=True, description="ID of an attribute."
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description="The list of reordering operations for given attribute values.",
        )

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /, **data):
        page_id = data["page_id"]
        page = cls.perform(page_id, "page", data, "pagevalueassignment", PageErrorCode)
        return PageReorderAttributeValues(page=page)

    @classmethod
    def get_instance(cls, instance_id: str):
        pk = cls.get_global_id_or_error(instance_id, only_type=Page, field="page_id")

        try:
            page = page_models.Page.objects.prefetch_related("attributes").get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "page_id": ValidationError(
                        (f"Couldn't resolve to a page: {instance_id}"),
                        code=PageErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return page
