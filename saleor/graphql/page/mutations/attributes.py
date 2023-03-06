from collections import defaultdict
from typing import Dict, List

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....attribute import AttributeType, models
from ....core.permissions import PagePermissions, PageTypePermissions
from ....core.tracing import traced_atomic_transaction
from ....page import models as page_models
from ....page.error_codes import PageErrorCode
from ...attribute.mutations import (
    BaseReorderAttributesMutation,
    BaseReorderAttributeValuesMutation,
)
from ...attribute.types import Attribute
from ...core import ResolveInfo
from ...core.inputs import ReorderInput
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, PageError
from ...core.utils.reordering import perform_reordering
from ...page.types import Page, PageType
from ...utils import resolve_global_ids_to_primary_keys


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
        description = "Assign attributes to a given page type."
        error_type_class = PageError
        error_type_field = "page_errors"
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)

    @classmethod
    def clean_attributes(
        cls,
        errors: Dict["str", List[ValidationError]],
        page_type: "page_models.PageType",
        attr_pks: List[int],
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
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)

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
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "page_type_id": ValidationError(
                        f"Couldn't resolve to a page type: {page_type_id}",
                        code=PageErrorCode.NOT_FOUND.value,
                    )
                }
            )

        page_attributes = page_type.attributepage.all()
        moves = data["moves"]

        try:
            operations = cls.prepare_operations(moves, page_attributes)
        except ValidationError as error:
            error.code = PageErrorCode.NOT_FOUND.value
            raise ValidationError({"moves": error})

        with traced_atomic_transaction():
            perform_reordering(page_attributes, operations)

        return PageTypeReorderAttributes(page_type=page_type)


class PageReorderAttributeValues(BaseReorderAttributeValuesMutation):
    page = graphene.Field(
        Page, description="Page from which attribute values are reordered."
    )

    class Meta:
        description = "Reorder page attribute values."
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
