import graphene

from ..core.doc_category import DOC_CATEGORY_DISCOUNTS
from ..core.scalars import JSON, PositiveDecimal
from ..core.types import BaseInputObjectType, NonNullList
from .enums import RewardValueTypeEnum


class ProductVariantPredicateInput(BaseInputObjectType):
    ids = NonNullList(graphene.ID, description="The list of product variant ids.")

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class ProductPredicateInput(BaseInputObjectType):
    ids = NonNullList(graphene.ID, description="The list of product ids.")

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class CategoryPredicateInput(BaseInputObjectType):
    ids = NonNullList(graphene.ID, description="The list of category ids.")

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class CollectionPredicateInput(BaseInputObjectType):
    ids = NonNullList(graphene.ID, description="The list of collection ids.")

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class PredicateInputObjectType(BaseInputObjectType):
    """Class for defining the predicate input.

    AND and OR class type fields are automatically added to available input
    fields, allowing to create complex filter statements.
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
            }
        )


class CataloguePredicateInput(PredicateInputObjectType):
    variant_predicate = ProductVariantPredicateInput(
        description="Defines the product variant conditions to be met."
    )
    product_predicate = ProductPredicateInput(
        description="Defines the product conditions to be met."
    )
    category_predicate = CategoryPredicateInput(
        description="Defines the category conditions to be met."
    )
    collection_predicate = CollectionPredicateInput(
        description="Defines the collection conditions to be met."
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionRuleBaseInput(BaseInputObjectType):
    name = graphene.String(description="Promotion rule name.")
    description = JSON(description="Promotion rule description.")
    catalogue_predicate = CataloguePredicateInput(
        description=(
            "Defines the conditions on the catalogue level that must be met "
            "for the reward to be applied."
        ),
    )
    reward_value_type = RewardValueTypeEnum(
        description=(
            "Defines the promotion rule reward value type. "
            "Must be provided together with reward value."
        ),
    )
    reward_value = PositiveDecimal(
        description=(
            "Defines the discount value. Required when catalogue predicate is provided."
        ),
    )
