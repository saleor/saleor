import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....core.tracing import traced_atomic_transaction
from ....page import models as page_models
from ....page.error_codes import PageErrorCode
from ....permission.enums import PageTypePermissions
from ...attribute.mutations import BaseReorderAttributesMutation
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.inputs import ReorderInput
from ...core.types import NonNullList, PageError
from ...core.utils.reordering import perform_reordering
from ...directives import doc
from ...page.types import PageType


@doc(category=DOC_CATEGORY_PAGES)
class PageTypeReorderAttributes(BaseReorderAttributesMutation):
    page_type = graphene.Field(
        PageType, description="Page type from which attributes are reordered."
    )

    class Arguments:
        page_type_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a page type."
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description="The list of attribute reordering operations.",
        )

    class Meta:
        description = "Reorder the attributes of a page type."
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        page_type_id = data["page_type_id"]
        pk = cls.get_global_id_or_error(page_type_id, only_type=PageType, field="pk")

        try:
            page_type = page_models.PageType.objects.prefetch_related(
                "attributepage"
            ).get(pk=pk)
        except ObjectDoesNotExist as e:
            raise ValidationError(
                {
                    "page_type_id": ValidationError(
                        f"Couldn't resolve to a page type: {page_type_id}",
                        code=PageErrorCode.NOT_FOUND.value,
                    )
                }
            ) from e

        page_attributes = page_type.attributepage.all()
        moves = data["moves"]

        try:
            operations = cls.prepare_operations(moves, page_attributes)
        except ValidationError as e:
            e.code = PageErrorCode.NOT_FOUND.value
            raise ValidationError({"moves": e}) from e

        with traced_atomic_transaction():
            perform_reordering(page_attributes, operations)

        return PageTypeReorderAttributes(page_type=page_type)
