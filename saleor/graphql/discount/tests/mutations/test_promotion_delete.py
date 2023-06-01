import graphene
import pytest

from ....tests.utils import assert_no_permission, get_graphql_content

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


def test_promotion_delete_by_staff_user(
    staff_api_client, permission_group_manage_discounts, promotion
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = staff_api_client.post_graphql(PROMOTION_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionDelete"]
    assert data["promotion"]["name"] == promotion.name
    with pytest.raises(promotion._meta.model.DoesNotExist):
        promotion.refresh_from_db()


def test_promotion_delete_by_staff_app(
    app_api_client, permission_manage_discounts, promotion
):
    # given
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = app_api_client.post_graphql(
        PROMOTION_DELETE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionDelete"]
    assert data["promotion"]["name"] == promotion.name
    with pytest.raises(promotion._meta.model.DoesNotExist):
        promotion.refresh_from_db()


def test_promotion_delete_by_customer(api_client, promotion):
    # given
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = api_client.post_graphql(PROMOTION_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)
