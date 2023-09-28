import graphene
import pytest
from django.core.exceptions import ValidationError

from ....discount.error_codes import PromotionCreateErrorCode
from ..mutations.promotion.validators import clean_predicate


def test_clean_predicate(variant, product):
    # given
    variant_ids = [graphene.Node.to_global_id("ProductVariant", variant.id)]
    product_ids = [graphene.Node.to_global_id("Product", product.id)]
    predicate = {
        "OR": [
            {"variant_predicate": {"ids": variant_ids}},
            {"product_predicate": {"ids": product_ids}},
        ]
    }

    # when
    response = clean_predicate(predicate, PromotionCreateErrorCode)

    # then
    assert response == {
        "OR": [
            {"variantPredicate": {"ids": variant_ids}},
            {"productPredicate": {"ids": product_ids}},
        ]
    }


@pytest.mark.parametrize(
    "predicate",
    [
        {
            "AND": [{"productPredicate": {"ids": ["ABC"]}}],
            "OR": [{"productPredicate": {"ids": ["ABC"]}}],
        },
        {
            "AND": [
                {
                    "productPredicate": {"ids": ["ABC"]},
                    "OR": [{"productPredicate": {"ids": ["ABC"]}}],
                }
            ]
        },
    ],
)
def test_clean_predicate_invalid_predicate(predicate):
    # when
    with pytest.raises(ValidationError) as validation_error:
        clean_predicate(predicate, PromotionCreateErrorCode)

    # then
    assert validation_error.value.code == PromotionCreateErrorCode.INVALID.value
