import graphene

from ....permission.enums import PageTypePermissions
from ...attribute.types import Attribute
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, PageError
from ...page.types import PageType
from ...utils import resolve_global_ids_to_primary_keys


class PageAttributeUnassign(BaseMutation):
    page_type = graphene.Field(PageType, description="The updated page type.")

    class Arguments:
        page_type_id = graphene.ID(
            required=True,
            description=(
                "ID of the page type from which the attributes should be unassign."
            ),
        )
        attribute_ids = NonNullList(
            graphene.ID,
            required=True,
            description="The IDs of the attributes to unassign.",
        )

    class Meta:
        description = "Unassign attributes from a given page type."
        doc_category = DOC_CATEGORY_PAGES
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        page_type_id = data["page_type_id"]
        attribute_ids = data["attribute_ids"]

        # retrieve the requested page type
        page_type = cls.get_node_or_error(info, page_type_id, only_type=PageType)

        # resolve all passed attributes IDs to attributes pks
        _, attr_pks = resolve_global_ids_to_primary_keys(attribute_ids, Attribute)

        page_type.page_attributes.remove(*attr_pks)

        return cls(page_type=page_type)
