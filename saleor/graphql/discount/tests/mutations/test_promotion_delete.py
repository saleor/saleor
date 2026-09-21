from unittest.mock import patch

import graphene
import pytest

from .....discount.error_codes import PromotionDeleteErrorCode
from .....discount.models import Promotion, PromotionRule
from .....product.models import ProductChannelListing
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...utils import get_products_for_promotion

PROMOTION_DELETE_MUTATION = """
    mutation promotionDelete($id: ID!) {
        promotionDelete(id: $id) {
            promotion {
                name
                id
            }
            errors {
                field
                code
                message
            }
            }
        }
"""


DELETE_PROMOTION_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation deletePromotion($id: ID, $externalReference: String) {
        promotionDelete(id: $id, externalReference: $externalReference) {
            promotion {
                name
                externalReference
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_delete_promotion_by_external_reference(
    staff_api_client, catalogue_promotion, permission_manage_discounts
):
    # given
    external_reference = "test-ext-ref"
    catalogue_promotion.external_reference = external_reference
    catalogue_promotion.save(update_fields=["external_reference"])
    variables = {"externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        DELETE_PROMOTION_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["promotionDelete"]
    assert data["errors"] == []
    assert data["promotion"]["name"] == catalogue_promotion.name
    assert data["promotion"]["externalReference"] == external_reference
    assert Promotion.objects.filter(pk=catalogue_promotion.pk).exists() is False


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            PromotionDeleteErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            PromotionDeleteErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            PromotionDeleteErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            PromotionDeleteErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'external_reference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            PromotionDeleteErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    catalogue_promotion,
    permission_manage_discounts,
    mocker,
):
    # given
    catalogue_promotion.external_reference = "existing-reference"
    catalogue_promotion.save(update_fields=("external_reference",))
    original_name = catalogue_promotion.name
    original_reference = catalogue_promotion.external_reference
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id(
            "Promotion", catalogue_promotion.pk
        )

    # when
    response = staff_api_client.post_graphql(
        DELETE_PROMOTION_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["promotionDelete"]
    assert data["promotion"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    catalogue_promotion.refresh_from_db(fields=("name", "external_reference"))
    assert catalogue_promotion.name == original_name
    assert catalogue_promotion.external_reference == original_reference
    webhook.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    catalogue_promotion,
    permission_manage_discounts,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    catalogue_promotion.external_reference = "existing-reference"
    catalogue_promotion.save(update_fields=("external_reference",))
    original_name = catalogue_promotion.name
    original_reference = catalogue_promotion.external_reference
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
    variables = {"externalReference": original_reference}

    # when
    response = client.post_graphql(
        DELETE_PROMOTION_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["promotionDelete"]
        assert data["errors"] == []
        assert Promotion.objects.filter(pk=catalogue_promotion.pk).exists() is False
        assert data["promotion"] == {
            "name": original_name,
            "externalReference": original_reference,
        }
        webhook.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"promotionDelete": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["promotionDelete"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: MANAGE_DISCOUNTS"
        )
        catalogue_promotion.refresh_from_db(fields=("name", "external_reference"))
        assert catalogue_promotion.name == original_name
        assert catalogue_promotion.external_reference == original_reference
        webhook.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
def test_promotion_delete_by_staff_user(
    promotion_deleted_mock,
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion = catalogue_promotion
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}
    PromotionRuleChannel = PromotionRule.channels.through
    channels_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    products_ids = list(
        get_products_for_promotion(promotion).values_list("id", flat=True)
    )

    # when
    response = staff_api_client.post_graphql(PROMOTION_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionDelete"]
    assert data["promotion"]["name"] == promotion.name

    promotion_deleted_mock.assert_called_once_with(promotion)

    with pytest.raises(promotion._meta.model.DoesNotExist):
        promotion.refresh_from_db()

    for listing in ProductChannelListing.objects.filter(
        channel_id__in=channels_ids, product_id__in=products_ids
    ):
        assert listing.discounted_price_dirty is True


@patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
def test_promotion_delete_by_staff_app(
    promotion_deleted_mock,
    app_api_client,
    permission_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}
    PromotionRuleChannel = PromotionRule.channels.through
    channels_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    products_ids = list(
        get_products_for_promotion(promotion).values_list("id", flat=True)
    )

    # when
    response = app_api_client.post_graphql(
        PROMOTION_DELETE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionDelete"]
    assert data["promotion"]["name"] == promotion.name

    promotion_deleted_mock.assert_called_once_with(promotion)

    with pytest.raises(promotion._meta.model.DoesNotExist):
        promotion.refresh_from_db()

    for listing in ProductChannelListing.objects.filter(
        channel_id__in=channels_ids, product_id__in=products_ids
    ):
        assert listing.discounted_price_dirty is True


@patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
def test_promotion_delete_by_customer(
    promotion_deleted_mock,
    api_client,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}
    PromotionRuleChannel = PromotionRule.channels.through
    channels_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    products_ids = list(
        get_products_for_promotion(promotion).values_list("id", flat=True)
    )

    # when
    response = api_client.post_graphql(PROMOTION_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)

    promotion_deleted_mock.assert_not_called()
    for listing in ProductChannelListing.objects.filter(
        channel_id__in=channels_ids, product_id__in=products_ids
    ):
        assert listing.discounted_price_dirty is False
