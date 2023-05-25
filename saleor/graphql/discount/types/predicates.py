import graphene

from ...core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.types import BaseObjectType, NonNullList


class PredicateObjectType(BaseObjectType):
    """Class for defining the predicate type with additional operators: AND, OR.

    AND and OR class type fields are automatically added to type fields.
    """

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, **options):
        super().__init_subclass_with_meta__(_meta=_meta, **options)
        cls._meta.fields.update(
            {
                "AND": graphene.Field(
                    NonNullList(
                        cls,
                    ),
                    description="List of conditions that must be met.",
                ),
                "OR": graphene.Field(
                    NonNullList(
                        cls,
                    ),
                    description=(
                        "A list of conditions of which at least one must be met."
                    ),
                ),
                # TODO: needs optimization
                # "NOT": graphene.Field(
                #     cls, description="A condition that cannot be met."
                # ),
            }
        )


class ProductPredicate(BaseObjectType):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the Product type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS


class ProductVariantPredicate(BaseObjectType):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the ProductVariant type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS


class CategoryPredicate(BaseObjectType):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the Category type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS


class CollectionPredicate(BaseObjectType):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the Collection type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS


class CatalogueObjectsPredicate(graphene.Union):
    class Meta:
        types = (
            ProductPredicate,
            ProductVariantPredicate,
            CategoryPredicate,
            CollectionPredicate,
        )


class CataloguePredicate(PredicateObjectType):
    predicate = graphene.Field(
        CatalogueObjectsPredicate, description="Represents the catalogue predicate."
    )
