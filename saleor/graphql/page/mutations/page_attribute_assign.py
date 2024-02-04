from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....attribute import AttributeType, models
from ....page import models as page_models
from ....page.error_codes import PageErrorCode
from ....permission.enums import PageTypePermissions
from ...attribute.types import Attribute
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, PageError
from ...page.types import PageType


class PageAttributeAssign(BaseMutation):
    page_type = graphene.Field(PageType, description="The updated page type.")

    class Arguments:
        page_type_id = graphene.ID(
            required=True,
            description="ID of the page type to assign the attributes into.",
        )
        attribute_ids = NonNullList(
            graphene.ID,
            required=True,
            description="The IDs of the attributes to assign.",
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        description = "Assign attributes to a given page type."
        error_type_class = PageError
        error_type_field = "page_errors"
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)

    @classmethod
    def clean_attributes(
        cls,
        errors: dict["str", list[ValidationError]],
        page_type: "page_models.PageType",
        attr_pks: list[int],
    ):
        """Ensure the attributes are page attributes and are not already assigned."""

        # check if any attribute is not a page type
        invalid_attributes = models.Attribute.objects.filter(pk__in=attr_pks).exclude(
            type=AttributeType.PAGE_TYPE
        )

        if invalid_attributes:
            invalid_attributes_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in invalid_attributes
            ]
            error = ValidationError(
                "Only page attributes can be assigned.",
                code=PageErrorCode.INVALID.value,
                params={"attributes": invalid_attributes_ids},
            )
            errors["attribute_ids"].append(error)

        # check if any attribute is already assigned to this page type
        assigned_attrs = models.Attribute.objects.get_assigned_page_type_attributes(
            page_type.pk
        ).filter(pk__in=attr_pks)

        if assigned_attrs:
            assigned_attributes_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in assigned_attrs
            ]
            error = ValidationError(
                "Some of the attributes have been already assigned to this page type.",
                code=PageErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.value,
                params={"attributes": assigned_attributes_ids},
            )
            errors["attribute_ids"].append(error)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, attribute_ids, page_type_id
    ):
        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)

        # retrieve the requested page type
        page_type = cls.get_node_or_error(
            info, page_type_id, only_type=PageType, field="page_type_id"
        )

        # resolve all passed attributes IDs to attributes pks
        attr_pks = cls.get_global_ids_or_error(
            attribute_ids, Attribute, field="attribute_ids"
        )

        # ensure the attributes are assignable
        cls.clean_attributes(errors, page_type, attr_pks)

        if errors:
            raise ValidationError(errors)

        page_type.page_attributes.add(*attr_pks)

        return cls(page_type=page_type)
