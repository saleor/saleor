from ....tests.utils import get_graphql_content

QUERY_GET_VARIANTS_FROM_ORDER = """
{
  me{
    orders(first:10){
      edges{
        node{
          lines{
            variant{
              id
            }
          }
        }
      }
    }
  }
}
"""


def test_get_variant_from_order_line_variant_published_as_customer(
    user_api_client, order_line
):
    # given

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_published_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_published_as_customer(
    user_api_client, order_line
):
    # given
    product = order_line.variant.product
    product.channel_listings.update(is_published=False)

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None


def test_get_variant_from_order_line_variant_not_published_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    product = order_line.variant.product
    product.channel_listings.update(is_published=False)

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_assigned_to_channel_as_customer(
    user_api_client, order_line
):
    # given
    product = order_line.variant.product
    product.channel_listings.all().delete()

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None


def test_get_variant_from_order_line_variant_not_assigned_to_channel_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    product = order_line.variant.product
    product.channel_listings.all().delete()

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_visible_in_listings_as_customer(
    user_api_client, order_line
):
    # given
    product = order_line.variant.product
    product.channel_listings.update(visible_in_listings=False)

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_visible_in_listings_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    product = order_line.variant.product
    product.channel_listings.update(visible_in_listings=False)

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_exists_as_customer(
    user_api_client, order_line
):
    # given
    order_line.variant = None
    order_line.save()

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None


def test_get_variant_from_order_line_variant_not_exists_as_staff(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    order_line.variant = None
    order_line.save()

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None
