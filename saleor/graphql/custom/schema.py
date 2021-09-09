import graphene
from django.core.exceptions import ValidationError
from graphql_relay import from_global_id

from saleor.custom.error_codes import CategoryCustomErrorCode
from saleor.custom.models import CategoryCustom
from saleor.graphql.custom.mutations.customs import (
    CategoryCustomCreate,
    CategoryCustomDelete,
    CategoryCustomUpdate,
)
from saleor.graphql.custom.types import CategoryCustomType


class CategoryCustomQueries(graphene.ObjectType):
    category_custom = graphene.Field(
        CategoryCustomType,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the category custom.",
        ),
        slug=graphene.Argument(
            graphene.String,
            description="slug of the category custom.",
        ),
        description="Detail of the category custom.",
    )

    categories_custom = graphene.List(
        CategoryCustomType,
        description="List of the category custom.",
    )

    def resolve_categories_custom(root, info, **kwargs):
        slug = kwargs.get("slug")
        rs = CategoryCustom.objects.filter(is_deleted=False)
        if slug:
            rs = rs.filter(slug__contains=slug)
        return rs

    def resolve_category_custom(root, info, id=None, slug=None, **kwargs):
        try:
            if id:
                _, _id = from_global_id(id)
                rs = CategoryCustom.objects.filter(is_deleted=False, id=_id)
            else:
                rs = CategoryCustom.objects.filter(slug=slug)
            return rs.first()
        except CategoryCustom.DoesNotExist:
            raise ValidationError(
                {
                    "operations": ValidationError(
                        "Category custom not found.",
                        code=CategoryCustomErrorCode.NOT_FOUND,
                    )
                }
            )


class CategoryCustomMutations(graphene.ObjectType):
    category_custom_create = CategoryCustomCreate.Field()
    category_custom_update = CategoryCustomUpdate.Field()
    category_custom_delete = CategoryCustomDelete.Field()
