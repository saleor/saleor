import graphene

from ...core import ResolveInfo
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


class BaseCataloguePredicate(BaseObjectType):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    @classmethod
    def resolve_ids(cls, root, _info: ResolveInfo):
        return [graphene.Node.to_global_id(cls.type_name, id) for id in root.ids]

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=(),
        possible_types=(),
        default_resolver=None,
        _meta=None,
        doc_category=None,
        type_name=None,
        **options,
    ):
        cls.doc_category = doc_category
        cls.type_name = type_name
        super(BaseObjectType, cls).__init_subclass_with_meta__(
            interfaces=interfaces,
            possible_types=possible_types,
            default_resolver=default_resolver,
            _meta=_meta,
            **options,
        )


class ProductPredicate(BaseCataloguePredicate):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the Product type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS
        type_name = "Product"


class ProductVariantPredicate(BaseCataloguePredicate):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the ProductVariant type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS
        type_name = "ProductVariant"


class CategoryPredicate(BaseCataloguePredicate):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the Category type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS
        type_name = "Category"


class CollectionPredicate(BaseCataloguePredicate):
    ids = NonNullList(graphene.ID, description="List of channel ids.")

    class Meta:
        description = (
            "Represents the predicate for the Collection type."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS
        type_name = "Collection"


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

    class Meta:
        description = (
            "Represents the predicate for the catalogue."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_DISCOUNTS

    @staticmethod
    def resolve_predicate(root, info: ResolveInfo):
        if variant_predicate := root.pop("variantPredicate", []):
            return ProductVariantPredicate(**variant_predicate)
        if product_predicate := root.pop("productPredicate", []):
            return ProductPredicate(**product_predicate)
        if collection_predicate := root.pop("collectionPredicate", []):
            return CollectionPredicate(**collection_predicate)
        if category_predicate := root.pop("categoryPredicate", []):
            return CategoryPredicate(**category_predicate)
        return None
