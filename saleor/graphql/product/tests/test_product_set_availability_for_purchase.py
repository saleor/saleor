import datetime

import graphene

from ....product.error_codes import ProductErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content

MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE = """
    mutation ProductSetAvailabilityForPurchase(
        $id: ID!, $is_available: Boolean!, $start_date: Date
    ) {
        productSetAvailabilityForPurchase(
            productId: $id, isAvailable: $is_available, startDate: $start_date
        ) {
            product {
                isAvailableForPurchase
                availableForPurchase
            }
            productErrors {
                code
                field
            }
        }
    }
"""


def test_product_set_availability_for_purchase_by_staff(
    staff_api_client, permission_manage_products, product
):
    # given
    query = MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE

    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_products)

    start_date = datetime.date(1999, 1, 1)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "is_available": True,
        "start_date": start_date,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productSetAvailabilityForPurchase"]
    product_data = data["product"]

    assert not data["productErrors"]
    assert product_data["isAvailableForPurchase"] is True
    assert product_data["availableForPurchase"] == start_date.strftime("%Y-%m-%d")


def test_product_set_availability_for_purchase_by_staff_no_permissions(
    staff_api_client, product
):
    # given
    query = MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE

    start_date = datetime.date(1999, 1, 1)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "is_available": True,
        "start_date": start_date,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_product_set_availability_for_purchase_by_app(
    app_api_client, permission_manage_products, product
):
    # given
    query = MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE

    app = app_api_client.app
    app.permissions.add(permission_manage_products)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "is_available": True,
    }

    # when
    response = app_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productSetAvailabilityForPurchase"]
    product_data = data["product"]

    assert not data["productErrors"]
    assert product_data["isAvailableForPurchase"] is True
    assert product_data["availableForPurchase"] == datetime.date.today().strftime(
        "%Y-%m-%d"
    )


def test_product_set_availability_for_purchase_by_app_no_permissions(
    app_api_client, product
):
    # given
    query = MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE

    start_date = datetime.date(1999, 1, 1)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "is_available": True,
        "start_date": start_date,
    }

    # when
    response = app_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_product_set_availability_for_purchase_by_customer(user_api_client, product):
    # given
    query = MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE

    start_date = datetime.date(1999, 1, 1)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "is_available": True,
        "start_date": start_date,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_product_set_availability_for_purchase_is_available_false_and_start_date_given(
    staff_api_client, permission_manage_products, product
):
    # given
    query = MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE

    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_products)

    start_date = datetime.date(1999, 1, 1)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "is_available": False,
        "start_date": start_date,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productSetAvailabilityForPurchase"]
    product_data = data["product"]
    errors = data["productErrors"]

    assert not product_data
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["field"] == "startDate"


def test_product_set_availability_for_purchase_is_available_false(
    staff_api_client, permission_manage_products, product
):
    # given
    query = MUTATION_PRODUCT_SET_AVAILABILITY_FOR_PURCHASE

    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_products)

    product.available_for_purchase = datetime.date(1999, 1, 1)
    product.save(update_fields=["available_for_purchase"])

    assert product.available_for_purchase

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "is_available": False,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productSetAvailabilityForPurchase"]
    product_data = data["product"]

    assert not data["productErrors"]
    assert product_data["isAvailableForPurchase"] is False
    assert product_data["availableForPurchase"] is None
