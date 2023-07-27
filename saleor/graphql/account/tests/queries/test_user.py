from unittest.mock import MagicMock

import graphene
import mock
import pytest
from django.core.files import File

from .....account.models import Group
from .....channel.models import Channel
from .....order import OrderStatus
from .....order.models import FulfillmentStatus, Order
from .....thumbnail.models import Thumbnail
from ....core.enums import ThumbnailFormatEnum
from ....core.utils import to_global_id_or_none
from ....tests.utils import (
    assert_graphql_error_with_message,
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

FULL_USER_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            email
            firstName
            lastName
            isStaff
            isActive
            isConfirmed
            addresses {
                id
                isDefaultShippingAddress
                isDefaultBillingAddress
            }
            checkoutIds
            orders(first: 10) {
                totalCount
                edges {
                    node {
                        id
                        number
                    }
                }
            }
            languageCode
            dateJoined
            lastLogin
            defaultShippingAddress {
                firstName
                lastName
                companyName
                streetAddress1
                streetAddress2
                city
                cityArea
                postalCode
                countryArea
                phone
                country {
                    code
                }
                isDefaultShippingAddress
                isDefaultBillingAddress
            }
            defaultBillingAddress {
                firstName
                lastName
                companyName
                streetAddress1
                streetAddress2
                city
                cityArea
                postalCode
                countryArea
                phone
                country {
                    code
                }
                isDefaultShippingAddress
                isDefaultBillingAddress
            }
            avatar {
                url
            }
            userPermissions {
                code
                sourcePermissionGroups(userId: $id) {
                    name
                }
            }
            permissionGroups {
                name
                permissions {
                    code
                }
            }
            editableGroups {
                name
            }
            restrictedAccessToChannels
            accessibleChannels {
                slug
            }
            giftCards(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
            checkouts(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
"""


def test_query_customer_user(
    staff_api_client,
    customer_user,
    gift_card_used,
    gift_card_expiry_date,
    address,
    permission_manage_users,
    permission_manage_orders,
    media_root,
    settings,
    checkout,
):
    user = customer_user
    user.default_shipping_address.country = "US"
    user.default_shipping_address.save()
    user.addresses.add(address.get_copy())

    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save()

    checkout.user = user
    checkout.save()

    Group.objects.create(name="empty group")

    query = FULL_USER_QUERY
    ID = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": ID}
    staff_api_client.user.user_permissions.add(
        permission_manage_users, permission_manage_orders
    )
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert data["email"] == user.email
    assert data["firstName"] == user.first_name
    assert data["lastName"] == user.last_name
    assert data["isStaff"] == user.is_staff
    assert data["isActive"] == user.is_active
    assert data["isConfirmed"] == user.is_confirmed
    assert data["orders"]["totalCount"] == user.orders.count()
    assert data["avatar"]["url"]
    assert data["languageCode"] == settings.LANGUAGE_CODE.upper()
    assert len(data["editableGroups"]) == 0
    assert data["restrictedAccessToChannels"] is True
    assert len(data["accessibleChannels"]) == 0

    assert len(data["addresses"]) == user.addresses.count()
    for address in data["addresses"]:
        if address["isDefaultShippingAddress"]:
            address_id = graphene.Node.to_global_id(
                "Address", user.default_shipping_address.id
            )
            assert address["id"] == address_id
        if address["isDefaultBillingAddress"]:
            address_id = graphene.Node.to_global_id(
                "Address", user.default_billing_address.id
            )
            assert address["id"] == address_id

    address = data["defaultShippingAddress"]
    user_address = user.default_shipping_address
    assert address["firstName"] == user_address.first_name
    assert address["lastName"] == user_address.last_name
    assert address["companyName"] == user_address.company_name
    assert address["streetAddress1"] == user_address.street_address_1
    assert address["streetAddress2"] == user_address.street_address_2
    assert address["city"] == user_address.city
    assert address["cityArea"] == user_address.city_area
    assert address["postalCode"] == user_address.postal_code
    assert address["country"]["code"] == user_address.country.code
    assert address["countryArea"] == user_address.country_area
    assert address["phone"] == user_address.phone.as_e164
    assert address["isDefaultShippingAddress"] is None
    assert address["isDefaultBillingAddress"] is None

    address = data["defaultBillingAddress"]
    user_address = user.default_billing_address
    assert address["firstName"] == user_address.first_name
    assert address["lastName"] == user_address.last_name
    assert address["companyName"] == user_address.company_name
    assert address["streetAddress1"] == user_address.street_address_1
    assert address["streetAddress2"] == user_address.street_address_2
    assert address["city"] == user_address.city
    assert address["cityArea"] == user_address.city_area
    assert address["postalCode"] == user_address.postal_code
    assert address["country"]["code"] == user_address.country.code
    assert address["countryArea"] == user_address.country_area
    assert address["phone"] == user_address.phone.as_e164
    assert address["isDefaultShippingAddress"] is None
    assert address["isDefaultBillingAddress"] is None
    assert len(data["giftCards"]) == 1
    assert data["giftCards"]["edges"][0]["node"]["id"] == graphene.Node.to_global_id(
        "GiftCard", gift_card_used.pk
    )
    assert data["checkoutIds"] == [to_global_id_or_none(checkout)]
    assert data["checkouts"]["edges"][0]["node"]["id"] == graphene.Node.to_global_id(
        "Checkout", checkout.pk
    )


def test_query_customer_user_with_orders(
    staff_api_client,
    customer_user,
    order_list,
    permission_group_manage_orders,
    permission_manage_users,
):
    # given
    query = FULL_USER_QUERY
    order_unfulfilled = order_list[0]
    order_unfulfilled.user = customer_user

    order_unconfirmed = order_list[1]
    order_unconfirmed.status = OrderStatus.UNCONFIRMED
    order_unconfirmed.user = customer_user

    order_draft = order_list[2]
    order_draft.status = OrderStatus.DRAFT
    order_draft.user = customer_user

    Order.objects.bulk_update(
        [order_unconfirmed, order_draft, order_unfulfilled], ["user", "status"]
    )

    id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": id}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    user = content["data"]["user"]
    assert {order["node"]["id"] for order in user["orders"]["edges"]} == {
        graphene.Node.to_global_id("Order", order.pk) for order in order_list
    }


def test_query_customer_user_with_orders_no_manage_orders_perm(
    staff_api_client,
    customer_user,
    order_list,
    permission_manage_users,
):
    # given
    query = FULL_USER_QUERY
    order_unfulfilled = order_list[0]
    order_unfulfilled.user = customer_user

    order_unconfirmed = order_list[1]
    order_unconfirmed.status = OrderStatus.UNCONFIRMED
    order_unconfirmed.user = customer_user

    order_draft = order_list[2]
    order_draft.status = OrderStatus.DRAFT
    order_draft.user = customer_user

    Order.objects.bulk_update(
        [order_unconfirmed, order_draft, order_unfulfilled], ["user", "status"]
    )

    id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # then
    assert_no_permission(response)


def test_query_customer_user_app(
    app_api_client,
    customer_user,
    address,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    media_root,
    app,
):
    user = customer_user
    user.default_shipping_address.country = "US"
    user.default_shipping_address.save()
    user.addresses.add(address.get_copy())

    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save()

    Group.objects.create(name="empty group")

    query = FULL_USER_QUERY
    ID = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": ID}
    app.permissions.add(
        permission_manage_staff, permission_manage_users, permission_manage_orders
    )
    response = app_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert data["email"] == user.email


def test_query_customer_user_with_orders_by_app_no_manage_orders_perm(
    app_api_client,
    customer_user,
    order_list,
    permission_manage_users,
):
    # given
    query = FULL_USER_QUERY
    order_unfulfilled = order_list[0]
    order_unfulfilled.user = customer_user

    order_unconfirmed = order_list[1]
    order_unconfirmed.status = OrderStatus.UNCONFIRMED
    order_unconfirmed.user = customer_user

    order_draft = order_list[2]
    order_draft.status = OrderStatus.DRAFT
    order_draft.user = customer_user

    Order.objects.bulk_update(
        [order_unconfirmed, order_draft, order_unfulfilled], ["user", "status"]
    )

    id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # then
    assert_no_permission(response)


def test_query_customer_user_with_orders_restricted_access_to_channel(
    staff_api_client,
    customer_user,
    order_list,
    permission_group_all_perms_channel_USD_only,
    channel_USD,
    channel_PLN,
    channel_JPY,
):
    # given
    query = FULL_USER_QUERY
    order_unfulfilled = order_list[0]
    order_unfulfilled.user = customer_user
    order_unfulfilled.channel = channel_PLN

    order_unconfirmed = order_list[1]
    order_unconfirmed.status = OrderStatus.UNCONFIRMED
    order_unconfirmed.user = customer_user
    order_unconfirmed.channel = channel_USD

    order_draft = order_list[2]
    order_draft.status = OrderStatus.DRAFT
    order_draft.user = customer_user
    order_draft.channel = channel_JPY

    Order.objects.bulk_update(
        [order_unconfirmed, order_draft, order_unfulfilled],
        ["user", "status", "channel"],
    )

    id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": id}
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    user = content["data"]["user"]
    assert len(user["orders"]["edges"]) == 1
    assert user["orders"]["edges"][0]["node"]["number"] == str(order_unconfirmed.number)


def test_query_staff_user(
    staff_api_client,
    staff_user,
    address,
    permission_manage_users,
    media_root,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_menus,
):
    staff_user.user_permissions.add(permission_manage_orders, permission_manage_staff)

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="another user group"),
            Group(name="another group"),
            Group(name="empty group"),
        ]
    )
    group1, group2, group3, group4 = groups

    group1.permissions.add(permission_manage_users, permission_manage_products)

    # user groups
    staff_user.groups.add(group1, group2)

    # another group (not user group) with permission_manage_users
    group3.permissions.add(permission_manage_users, permission_manage_menus)

    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image2.jpg"
    staff_user.avatar = avatar_mock
    staff_user.save()

    query = FULL_USER_QUERY
    user_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": user_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["user"]

    assert data["email"] == staff_user.email
    assert data["firstName"] == staff_user.first_name
    assert data["lastName"] == staff_user.last_name
    assert data["isStaff"] == staff_user.is_staff
    assert data["isActive"] == staff_user.is_active
    assert data["orders"]["totalCount"] == staff_user.orders.count()
    assert data["avatar"]["url"]

    assert len(data["permissionGroups"]) == 2
    assert {group_data["name"] for group_data in data["permissionGroups"]} == {
        group1.name,
        group2.name,
    }
    assert len(data["userPermissions"]) == 4
    assert len(data["editableGroups"]) == Group.objects.count() - 1
    assert {data_group["name"] for data_group in data["editableGroups"]} == {
        group1.name,
        group2.name,
        group4.name,
    }
    assert data["restrictedAccessToChannels"] is False
    assert len(data["accessibleChannels"]) == Channel.objects.count()

    formated_user_permissions_result = [
        {
            "code": perm["code"].lower(),
            "groups": {group["name"] for group in perm["sourcePermissionGroups"]},
        }
        for perm in data["userPermissions"]
    ]
    all_permissions = group1.permissions.all() | staff_user.user_permissions.all()
    for perm in all_permissions:
        source_groups = {group.name for group in perm.group_set.filter(user=staff_user)}
        expected_data = {"code": perm.codename, "groups": source_groups}
        assert expected_data in formated_user_permissions_result


def test_query_staff_user_with_order_and_without_manage_orders_perm(
    staff_api_client,
    staff_user,
    order_list,
    permission_manage_staff,
    permission_group_no_perms_all_channels,
):
    # given
    permission_group_no_perms_all_channels.user_set.add(staff_user)
    staff_user.user_permissions.add(permission_manage_staff)

    order_unfulfilled = order_list[0]
    order_unfulfilled.user = staff_user

    order_unconfirmed = order_list[1]
    order_unconfirmed.status = OrderStatus.UNCONFIRMED
    order_unconfirmed.user = staff_user

    order_draft = order_list[2]
    order_draft.status = OrderStatus.DRAFT
    order_draft.user = staff_user

    Order.objects.bulk_update(
        [order_unconfirmed, order_draft, order_unfulfilled], ["user", "status"]
    )

    query = FULL_USER_QUERY
    user_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": user_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["user"]

    assert data["email"] == staff_user.email
    assert data["orders"]["totalCount"] == 2
    assert {node["node"]["id"] for node in data["orders"]["edges"]} == {
        graphene.Node.to_global_id("Order", order.pk)
        for order in [order_unfulfilled, order_unconfirmed]
    }


def test_query_staff_user_with_orders_and_manage_orders_perm(
    staff_api_client,
    staff_user,
    order_list,
    permission_manage_staff,
    permission_group_manage_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_user)
    staff_user.user_permissions.add(permission_manage_staff)

    order_unfulfilled = order_list[0]
    order_unfulfilled.user = staff_user

    order_unconfirmed = order_list[1]
    order_unconfirmed.status = OrderStatus.UNCONFIRMED
    order_unconfirmed.user = staff_user

    order_draft = order_list[2]
    order_draft.status = OrderStatus.DRAFT
    order_draft.user = staff_user

    Order.objects.bulk_update(
        [order_unconfirmed, order_draft, order_unfulfilled], ["user", "status"]
    )

    query = FULL_USER_QUERY
    user_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": user_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["user"]

    assert data["email"] == staff_user.email
    assert data["orders"]["totalCount"] == 3
    assert {node["node"]["id"] for node in data["orders"]["edges"]} == {
        graphene.Node.to_global_id("Order", order.pk)
        for order in [order_unfulfilled, order_unconfirmed, order_draft]
    }


USER_QUERY = """
    query User($id: ID $email: String, $externalReference: String) {
        user(id: $id, email: $email, externalReference: $externalReference) {
            id
            email
            externalReference
        }
    }
"""


def test_query_user_by_email_address(
    user_api_client, customer_user, permission_manage_users
):
    email = customer_user.email
    variables = {"email": email}
    response = user_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert customer_user.email == data["email"]


def test_query_user_by_external_reference(
    user_api_client, customer_user, permission_manage_users
):
    # given
    user = customer_user
    ext_ref = "test-ext-ref"
    user.external_reference = ext_ref
    user.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = user_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["user"]
    assert data["externalReference"] == user.external_reference


def test_query_user_by_id_and_email(
    user_api_client, customer_user, permission_manage_users
):
    email = customer_user.email
    id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {
        "id": id,
        "email": email,
    }
    response = user_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    assert_graphql_error_with_message(
        response, "Argument 'id' cannot be combined with 'email'"
    )


def test_customer_can_not_see_other_users_data(user_api_client, staff_user):
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id}
    response = user_api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)


def test_user_query_anonymous_user(api_client):
    variables = {"id": ""}
    response = api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)


def test_user_query_permission_manage_users_get_customer(
    staff_api_client, customer_user, permission_manage_users
):
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": customer_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert customer_user.email == data["email"]


def test_user_query_as_app(app_api_client, customer_user, permission_manage_users):
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": customer_id}
    response = app_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert customer_user.email == data["email"]


def test_user_query_permission_manage_users_get_staff(
    staff_api_client, staff_user, permission_manage_users
):
    staff_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": staff_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    assert not content["data"]["user"]


def test_user_query_permission_manage_staff_get_customer(
    staff_api_client, customer_user, permission_manage_staff
):
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": customer_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    assert not content["data"]["user"]


def test_user_query_permission_manage_staff_get_staff(
    staff_api_client, staff_user, permission_manage_staff
):
    staff_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": staff_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert staff_user.email == data["email"]


@pytest.mark.parametrize("id", ["'", "abc"])
def test_user_query_invalid_id(
    id, staff_api_client, customer_user, permission_manage_users
):
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )

    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["user"] is None


def test_user_query_object_with_given_id_does_not_exist(
    staff_api_client, permission_manage_users
):
    id = graphene.Node.to_global_id("User", -1)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )

    content = get_graphql_content(response)
    assert content["data"]["user"] is None


def test_user_query_object_with_invalid_object_type(
    staff_api_client, customer_user, permission_manage_users
):
    id = graphene.Node.to_global_id("Order", customer_user.pk)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )

    content = get_graphql_content(response)
    assert content["data"]["user"] is None


USER_AVATAR_QUERY = """
    query User($id: ID, $size: Int, $format: ThumbnailFormatEnum) {
        user(id: $id) {
            id
            avatar(size: $size, format: $format) {
                url
                alt
            }
        }
    }
"""


def test_query_user_avatar_with_size_and_format_proxy_url_returned(
    staff_api_client, media_root, permission_manage_staff, site_settings
):
    # given
    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save(update_fields=["avatar"])

    format = ThumbnailFormatEnum.WEBP.name

    user_id = graphene.Node.to_global_id("User", user.id)
    user_uuid = graphene.Node.to_global_id("User", user.uuid)
    variables = {"id": user_id, "size": 120, "format": format}

    # when
    response = staff_api_client.post_graphql(
        USER_AVATAR_QUERY, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    domain = site_settings.site.domain
    assert (
        data["avatar"]["url"]
        == f"http://{domain}/thumbnail/{user_uuid}/128/{format.lower()}/"
    )


def test_query_user_avatar_with_size_proxy_url_returned(
    staff_api_client, media_root, permission_manage_staff, site_settings
):
    # given
    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save(update_fields=["avatar"])

    user_id = graphene.Node.to_global_id("User", user.id)
    user_uuid = graphene.Node.to_global_id("User", user.uuid)
    variables = {"id": user_id, "size": 120}

    # when
    response = staff_api_client.post_graphql(
        USER_AVATAR_QUERY, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert (
        data["avatar"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{user_uuid}/128/"
    )


def test_query_user_avatar_with_size_thumbnail_url_returned(
    staff_api_client, media_root, permission_manage_staff, site_settings
):
    # given
    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save(update_fields=["avatar"])

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(user=user, size=128, image=thumbnail_mock)

    id = graphene.Node.to_global_id("User", user.pk)
    variables = {"id": id, "size": 120}

    # when
    response = staff_api_client.post_graphql(
        USER_AVATAR_QUERY, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert (
        data["avatar"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_query_user_avatar_original_size_custom_format_provided_original_image_returned(
    staff_api_client, media_root, permission_manage_staff, site_settings
):
    # given
    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save(update_fields=["avatar"])

    format = ThumbnailFormatEnum.WEBP.name

    id = graphene.Node.to_global_id("User", user.pk)
    variables = {"id": id, "format": format, "size": 0}

    # when
    response = staff_api_client.post_graphql(
        USER_AVATAR_QUERY, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert (
        data["avatar"]["url"]
        == f"http://{site_settings.site.domain}/media/user-avatars/{avatar_mock.name}"
    )


def test_query_user_avatar_no_size_value(
    staff_api_client, media_root, permission_manage_staff, site_settings
):
    # given
    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save(update_fields=["avatar"])

    id = graphene.Node.to_global_id("User", user.pk)
    variables = {"id": id}

    user_uuid = graphene.Node.to_global_id("User", user.uuid)

    # when
    response = staff_api_client.post_graphql(
        USER_AVATAR_QUERY, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert (
        data["avatar"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{user_uuid}/4096/"
    )


def test_query_user_avatar_no_image(staff_api_client, permission_manage_staff):
    # given
    user = staff_api_client.user

    id = graphene.Node.to_global_id("User", user.pk)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        USER_AVATAR_QUERY, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert data["id"]
    assert not data["avatar"]


USER_CHANNEL_ACCESSIBILITY_QUERY = """
    query User($id: ID) {
        user(id: $id) {
            id
            restrictedAccessToChannels
            accessibleChannels {
                slug
            }
        }
    }
"""


def test_query_user_channel_accessibility_restricted_access_to_channels(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
    channel_USD,
):
    # given
    user = staff_api_client.user
    user.groups.add(permission_group_all_perms_channel_USD_only)

    id = graphene.Node.to_global_id("User", user.pk)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        USER_CHANNEL_ACCESSIBILITY_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert data["id"]
    assert data["restrictedAccessToChannels"] is True
    assert len(data["accessibleChannels"]) == 1
    assert data["accessibleChannels"][0]["slug"] == channel_USD.slug


def test_query_user_channel_accessibility_not_restricted_access(
    staff_api_client,
    permission_group_all_perms_all_channels,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
    channel_USD,
):
    # given
    user = staff_api_client.user
    user.groups.add(
        permission_group_all_perms_all_channels,
        permission_group_all_perms_channel_USD_only,
    )

    id = graphene.Node.to_global_id("User", user.pk)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        USER_CHANNEL_ACCESSIBILITY_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert data["id"]
    assert data["restrictedAccessToChannels"] is False
    assert len(data["accessibleChannels"]) == Channel.objects.count()


def test_user_with_cancelled_fulfillments(
    staff_api_client,
    customer_user,
    permission_manage_users,
    permission_group_manage_orders,
    fulfilled_order_with_cancelled_fulfillment,
):
    query = """
    query User($id: ID!) {
        user(id: $id) {
            orders (first: 1) {
                edges {
                    node {
                        id
                        fulfillments {
                            status
                        }
                    }
                }
            }
        }
    }
    """
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": user_id}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    order_id = graphene.Node.to_global_id(
        "Order", fulfilled_order_with_cancelled_fulfillment.id
    )
    data = content["data"]["user"]
    order = data["orders"]["edges"][0]["node"]
    assert order["id"] == order_id
    fulfillments = order["fulfillments"]
    assert len(fulfillments) == 2
    assert fulfillments[0]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert fulfillments[1]["status"] == FulfillmentStatus.CANCELED.upper()


USER_FEDERATION_QUERY = """
  query GetUserInFederation($representations: [_Any]) {
    _entities(representations: $representations) {
      __typename
      ... on User {
        id
        email
      }
    }
  }
"""


def test_staff_query_user_by_id_for_federation(
    staff_api_client, customer_user, permission_manage_users
):
    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "representations": [
            {
                "__typename": "User",
                "id": customer_user_id,
            },
        ],
    }

    response = staff_api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "User",
            "id": customer_user_id,
            "email": customer_user.email,
        }
    ]


def test_staff_query_user_by_email_for_federation(
    staff_api_client, customer_user, permission_manage_users
):
    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "representations": [
            {
                "__typename": "User",
                "email": customer_user.email,
            },
        ],
    }

    response = staff_api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "User",
            "id": customer_user_id,
            "email": customer_user.email,
        }
    ]


def test_staff_query_user_by_id_without_permission_for_federation(
    staff_api_client, customer_user
):
    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "representations": [
            {
                "__typename": "User",
                "id": customer_user_id,
            },
        ],
    }

    response = staff_api_client.post_graphql(USER_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_staff_query_user_by_email_without_permission_for_federation(
    staff_api_client, customer_user
):
    variables = {
        "representations": [
            {
                "__typename": "User",
                "email": customer_user.email,
            },
        ],
    }

    response = staff_api_client.post_graphql(USER_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_customer_query_self_by_id_for_federation(user_api_client, customer_user):
    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "representations": [
            {
                "__typename": "User",
                "id": customer_user_id,
            },
        ],
    }

    response = user_api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "User",
            "id": customer_user_id,
            "email": customer_user.email,
        }
    ]


def test_customer_query_self_by_email_for_federation(user_api_client, customer_user):
    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "representations": [
            {
                "__typename": "User",
                "email": customer_user.email,
            },
        ],
    }

    response = user_api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "User",
            "id": customer_user_id,
            "email": customer_user.email,
        }
    ]


def test_customer_query_user_by_id_for_federation(
    user_api_client, customer_user, staff_user
):
    staff_user_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {
        "representations": [
            {
                "__typename": "User",
                "id": staff_user_id,
            },
        ],
    }

    response = user_api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_customer_query_user_by_email_for_federation(
    user_api_client, customer_user, staff_user
):
    variables = {
        "representations": [
            {
                "__typename": "User",
                "email": staff_user.email,
            },
        ],
    }

    response = user_api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_unauthenticated_query_user_by_id_for_federation(api_client, customer_user):
    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "representations": [
            {
                "__typename": "User",
                "id": customer_user_id,
            },
        ],
    }

    response = api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_unauthenticated_query_user_by_email_for_federation(api_client, customer_user):
    variables = {
        "representations": [
            {
                "__typename": "User",
                "email": customer_user.email,
            },
        ],
    }

    response = api_client.post_graphql(
        USER_FEDERATION_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


USER_QUERY_WITH_STORED_PAYMENT_METHODS = """
query User($id: ID, $channel: String!) {
  user(id: $id) {
    storedPaymentMethods(channel: $channel){
      id
      gateway{
        name
        id
        config{
          field
          value
        }
        currencies
      }
      paymentMethodId
      creditCardInfo{
        brand
        firstDigits
        lastDigits
        expMonth
        expYear
      }
      supportedPaymentFlows
      type
      name
      data
    }
  }
}
"""


@mock.patch("saleor.plugins.manager.PluginsManager.list_stored_payment_methods")
def test_query_customer_stored_payment_methods(
    mocked_list_stored_payment_methods,
    staff_api_client,
    permission_manage_users,
    customer_user,
    channel_USD,
):
    query = USER_QUERY_WITH_STORED_PAYMENT_METHODS
    staff_api_client.user.user_permissions.add(permission_manage_users)

    # when
    response = staff_api_client.post_graphql(
        query,
        variables={
            "channel": channel_USD.slug,
            "id": graphene.Node.to_global_id("User", customer_user.pk),
        },
    )

    # then
    assert not mocked_list_stored_payment_methods.called

    content = get_graphql_content(response)

    assert content["data"]["user"]["storedPaymentMethods"] == []
