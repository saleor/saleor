from unittest.mock import patch

import pytest
from django.test import override_settings

from ...checkout import AddressType
from ...plugins.manager import get_plugins_manager
from ...tests.utils import flush_post_commit_hooks
from ..models import Address, User
from ..utils import (
    get_user_groups_permissions,
    is_user_address_limit_reached,
    remove_staff_member,
    remove_the_oldest_user_address,
    remove_the_oldest_user_address_if_address_limit_is_reached,
    retrieve_user_by_email,
    send_user_event,
    store_user_address,
)


def test_remove_staff_member_with_orders(staff_user, permission_manage_products, order):
    # given
    order.user = staff_user
    order.save()
    staff_user.user_permissions.add(permission_manage_products)

    # when
    remove_staff_member(staff_user)

    # then
    staff_user = User.objects.get(pk=staff_user.pk)
    assert not staff_user.is_staff
    assert not staff_user.user_permissions.exists()


def test_remove_staff_member(staff_user):
    # when
    remove_staff_member(staff_user)

    # then
    assert not User.objects.filter(pk=staff_user.pk).exists()


@override_settings(MAX_USER_ADDRESSES=2)
def test_is_user_address_limit_reached_true(customer_user, address):
    """Ensure that true is returned when a user has max amount of addresses assigned."""
    # given
    same_address = Address.objects.create(**address.as_data())
    customer_user.addresses.set([address, same_address])

    # when
    limit_reached = is_user_address_limit_reached(customer_user)

    # then
    assert limit_reached is True


@override_settings(MAX_USER_ADDRESSES=2)
def test_is_user_address_limit_reached_false(customer_user, address):
    # given
    customer_user.addresses.set([address])

    # when
    limit_reached = is_user_address_limit_reached(customer_user)

    # then
    assert limit_reached is False


def test_store_user_address_uses_existing_one(address):
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.add(address)

    expected_user_addresses_count = 1

    manager = get_plugins_manager(allow_replica=False)
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id == address.pk


def test_store_user_address_uses_existing_one_despite_duplicated(address):
    same_address = Address.objects.create(**address.as_data())
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.set([address, same_address])

    expected_user_addresses_count = 2

    manager = get_plugins_manager(allow_replica=False)
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id == address.pk


def test_store_user_address_create_new_address_if_not_associated(address):
    user = User.objects.create_user("test@example.com", "password")
    expected_user_addresses_count = 1

    manager = get_plugins_manager(allow_replica=False)
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id != address.pk


@override_settings(MAX_USER_ADDRESSES=2)
def test_store_user_address_address_not_saved(address):
    """Test that the address count does never exceeds the limit."""
    same_address = Address.objects.create(**address.as_data())
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.set([address, same_address])

    address_count = user.addresses.count()

    manager = get_plugins_manager(allow_replica=False)
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == address_count


def test_remove_the_oldest_user_address(customer_user, address):
    # given
    addresses = Address.objects.bulk_create(
        [Address(**address.as_data()) for i in range(5)]
    )

    customer_user.addresses.set(addresses)

    customer_user.default_billing_address = addresses[0]
    customer_user.default_shipping_address = addresses[1]
    customer_user.save(
        update_fields=["default_billing_address", "default_shipping_address"]
    )

    address_count = customer_user.addresses.count()

    # when
    remove_the_oldest_user_address(customer_user)

    # then
    with pytest.raises(addresses[2]._meta.model.DoesNotExist):
        addresses[2].refresh_from_db()

    assert customer_user.addresses.count() == address_count - 1


@override_settings(MAX_USER_ADDRESSES=2)
@patch("saleor.account.utils.remove_the_oldest_user_address")
def test_remove_the_oldest_user_address_if_address_limit_is_reached_limit_not_reached(
    remove_the_oldest_user_address_mock, customer_user, address
):
    # given
    customer_user.addresses.set([address])

    # when
    remove_the_oldest_user_address_if_address_limit_is_reached(customer_user)

    # then
    remove_the_oldest_user_address_mock.assert_not_called()


@override_settings(MAX_USER_ADDRESSES=2)
@patch("saleor.account.utils.remove_the_oldest_user_address")
def test_remove_the_oldest_user_address_if_address_limit_is_reached_limit_reached(
    remove_the_oldest_user_address_mock, customer_user, address
):
    # given
    same_address = Address.objects.create(**address.as_data())
    customer_user.addresses.set([address, same_address])

    # when
    remove_the_oldest_user_address_if_address_limit_is_reached(customer_user)

    # then
    remove_the_oldest_user_address_mock.assert_called_with(customer_user)


@pytest.fixture
def users_with_similar_emails():
    users = User.objects.bulk_create(
        [
            User(email="andrew@example.com"),
            User(email="Andrew@example.com"),
            User(email="john@example.com"),
            User(email="Susan@example.com"),
            User(email="Cindy@example.com"),
            User(email="CINDY@example.com"),
        ]
    )
    return users


@pytest.mark.parametrize(
    ("email", "expected_user"),
    [
        ("andrew@example.com", 0),
        ("Andrew@example.com", 1),
        ("ANDREW@example.com", 0),
        ("john@example.com", 2),
        ("John@example.com", 2),
        ("Susan@example.com", 3),
        ("susan@example.com", 3),
        ("Cindy@example.com", 4),
        ("cindy@example.com", None),
        ("CiNdY@example.com", None),
        ("non_existing_email@example.com", None),
    ],
)
def test_email_case_sensitivity(email, expected_user, users_with_similar_emails):
    # given
    users: list[User] = users_with_similar_emails
    # when
    user = retrieve_user_by_email(email=email)
    # then
    assert user == users[expected_user] if expected_user is not None else user is None


def get_user_groups_permissions_user_without_any_group(staff_user):
    # when
    permissions = get_user_groups_permissions(staff_user)

    # then
    assert not permissions


def get_user_groups_permissions_user(
    staff_user, permission_group_manage_orders, permission_group_manage_shipping
):
    # given
    staff_user.groups.add(
        permission_group_manage_orders, permission_group_manage_shipping
    )

    # when
    permissions = get_user_groups_permissions(staff_user)

    # then
    assert permissions.count() == 2


@patch("saleor.plugins.manager.PluginsManager.customer_updated")
@patch("saleor.plugins.manager.PluginsManager.customer_created")
@patch("saleor.plugins.manager.PluginsManager.staff_updated")
@patch("saleor.plugins.manager.PluginsManager.staff_created")
def test_send_user_event_no_webhook_sent(
    mock_staff_created_webhook,
    mock_staff_updated_webhook,
    mock_customer_created_webhook,
    mock_customer_updated_webhook,
    customer_user,
):
    # when
    send_user_event(customer_user, False, False)

    # then
    flush_post_commit_hooks()
    mock_staff_created_webhook.assert_not_called()
    mock_staff_updated_webhook.assert_not_called()
    mock_customer_created_webhook.assert_not_called()
    mock_customer_updated_webhook.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.customer_updated")
@patch("saleor.plugins.manager.PluginsManager.customer_created")
@patch("saleor.plugins.manager.PluginsManager.staff_updated")
@patch("saleor.plugins.manager.PluginsManager.staff_created")
def test_send_user_event_customer_created_event(
    mock_staff_created_webhook,
    mock_staff_updated_webhook,
    mock_customer_created_webhook,
    mock_customer_updated_webhook,
    customer_user,
):
    # when
    send_user_event(customer_user, True, True)

    # then
    flush_post_commit_hooks()
    mock_customer_created_webhook.assert_called_once_with(customer_user)
    mock_customer_updated_webhook.assert_not_called()
    mock_staff_created_webhook.assert_not_called()
    mock_staff_updated_webhook.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.customer_updated")
@patch("saleor.plugins.manager.PluginsManager.customer_created")
@patch("saleor.plugins.manager.PluginsManager.staff_updated")
@patch("saleor.plugins.manager.PluginsManager.staff_created")
def test_send_user_event_customer_updated_event(
    mock_staff_created_webhook,
    mock_staff_updated_webhook,
    mock_customer_created_webhook,
    mock_customer_updated_webhook,
    customer_user,
):
    # when
    send_user_event(customer_user, False, True)

    # then
    flush_post_commit_hooks()
    mock_customer_updated_webhook.assert_called_once_with(customer_user)
    mock_customer_created_webhook.assert_not_called()
    mock_staff_created_webhook.assert_not_called()
    mock_staff_updated_webhook.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.customer_updated")
@patch("saleor.plugins.manager.PluginsManager.customer_created")
@patch("saleor.plugins.manager.PluginsManager.staff_updated")
@patch("saleor.plugins.manager.PluginsManager.staff_created")
def test_send_user_event_staff_created_event(
    mock_staff_created_webhook,
    mock_staff_updated_webhook,
    mock_customer_created_webhook,
    mock_customer_updated_webhook,
    staff_user,
):
    # when
    send_user_event(staff_user, True, True)

    # then
    flush_post_commit_hooks()
    mock_staff_created_webhook.assert_called_once_with(staff_user)
    mock_staff_updated_webhook.assert_not_called()
    mock_customer_created_webhook.assert_not_called()
    mock_customer_updated_webhook.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.customer_updated")
@patch("saleor.plugins.manager.PluginsManager.customer_created")
@patch("saleor.plugins.manager.PluginsManager.staff_updated")
@patch("saleor.plugins.manager.PluginsManager.staff_created")
def test_send_user_event_staff_updated_event(
    mock_staff_created_webhook,
    mock_staff_updated_webhook,
    mock_customer_created_webhook,
    mock_customer_updated_webhook,
    staff_user,
):
    # when
    send_user_event(staff_user, False, True)

    # then
    flush_post_commit_hooks()
    mock_staff_updated_webhook.assert_called_once_with(staff_user)
    mock_staff_created_webhook.assert_not_called()
    mock_customer_created_webhook.assert_not_called()
    mock_customer_updated_webhook.assert_not_called()
