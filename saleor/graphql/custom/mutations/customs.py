import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from graphene_django import DjangoObjectType
from graphql_relay import from_global_id

from saleor.account.error_codes import AccountErrorCode
from saleor.custom import models
from saleor.custom.error_codes import CategoryCustomErrorCode
from saleor.custom.models import CategoryCustom
from saleor.graphql.attribute.descriptions import AttributeValueDescriptions
from saleor.graphql.channel.utils import validate_channel
from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.types.common import CategoryCustomError
from saleor.graphql.custom.resolvers import check_slug_exists
from saleor.plugins.category.plugin import send_category_notification


class CategoryCustomInput(graphene.InputObjectType):
    name = graphene.String(description="Category custom name.")
    slug = graphene.String(description="Category custom slug.")


class CategoryCustomTypeMutation(DjangoObjectType):
    id = graphene.ID
    name = graphene.String()
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)

    class Meta:
        description = "Represents an item in the checkout."
        interfaces = [graphene.relay.Node]
        model = models.CategoryCustom


class CategoryCustomCreate(BaseMutation):
    category_custom = graphene.Field(CategoryCustomTypeMutation)

    class Arguments:
        input = CategoryCustomInput(
            required=True, description="Fields required to create a category custom."
        )

    class Meta:
        description = "Creates a new category."
        model = models.CategoryCustom
        permissions = ()
        error_type_class = CategoryCustomError
        error_type_field = "category_custom_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        data = data.get("input")
        name = data.get("name")
        slug = data.get("slug")
        channel_slug = data.get("channel")

        if channel_slug is not None:
            channel_slug = validate_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug

        check_slug_exists(slug)

        category_custom = CategoryCustom.objects.create(name=name, slug=slug)
        send_category_notification(
            info.context.plugins,
            channel_slug=channel_slug,
        )
        return CategoryCustomCreate(category_custom=category_custom)


class CategoryCustomUpdate(BaseMutation):
    category_custom = graphene.Field(CategoryCustomTypeMutation)

    class Arguments:
        category_custom_id = graphene.ID(
            required=True,
            description="ID of product that media order will be altered.",
        )
        input = CategoryCustomInput(
            required=True, description="Fields required to create a category custom."
        )

    class Meta:
        description = "Creates a new category."
        model = models.CategoryCustom
        permissions = ()
        error_type_class = CategoryCustomError
        error_type_field = "category_custom_errors"

    @classmethod
    def perform_mutation(cls, root, info, category_custom_id, **data):
        _, _id = from_global_id(category_custom_id)
        try:
            category_custom = CategoryCustom.objects.get(id=_id, is_deleted=False)
        except CategoryCustom.DoesNotExist:
            raise ValidationError(
                {
                    "CategoryCustom": ValidationError(
                        "CategoryCustom not found.",
                        code=CategoryCustomErrorCode.NOT_FOUND,
                    )
                }
            )
        data = data.get("input")
        name = data.get("name")
        slug = data.get("slug")

        if category_custom.slug != slug:
            check_slug_exists(slug)
        try:
            with transaction.atomic():
                category_custom = category_custom.objects.select_for_update().get(
                    id=_id
                )
                category_custom.name = name
                category_custom.slug = slug
                category_custom.save()
        except Exception:
            raise ValidationError(
                {
                    "CategoryCustom": ValidationError(
                        "CategoryCustom delete error.",
                        code=CategoryCustomErrorCode.GRAPHQL_ERROR,
                    )
                }
            )
        return CategoryCustomUpdate(category_custom=category_custom)


class CategoryCustomDelete(BaseMutation):
    message = graphene.String()

    class Arguments:
        category_custom_id = graphene.ID(
            required=True,
            description="ID of product that media order will be altered.",
        )

    class Meta:
        description = "Creates a new category."
        model = models.CategoryCustom
        permissions = ()
        error_type_class = CategoryCustomError
        error_type_field = "category_custom_errors"

    @classmethod
    def perform_mutation(cls, root, info, category_custom_id, **data):
        _, _id = from_global_id(category_custom_id)
        try:
            category_custom = CategoryCustom.objects.select_for_update().filter(id=_id)
            category_custom.is_deleted = True
            category_custom.save()
            return CategoryCustomDelete(message="Success")
        except CategoryCustom.DoesNotExist:
            raise ValidationError(
                {
                    "CategoryCustom": ValidationError(
                        "CategoryCustom not found.",
                        code=CategoryCustomErrorCode.NOT_FOUND,
                    )
                }
            )
        except Exception:
            raise ValidationError(
                {
                    "CategoryCustom": ValidationError(
                        "CategoryCustom delete error.",
                        code=CategoryCustomErrorCode.GRAPHQL_ERROR,
                    )
                }
            )
