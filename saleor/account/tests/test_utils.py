from unittest.mock import patch

import pytest
from django.test import override_settings

from ...checkout import AddressType
from ...plugins.manager import get_plugins_manager
from ..models import Address, User
from ..utils import (
    is_user_address_limit_reached,
    remove_staff_member,
    remove_the_oldest_user_address,
    remove_the_oldest_user_address_if_address_limit_is_reached,
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
    """Ensure that false is returned when a user has less max amount
    of addresses assigned."""
    # given
    customer_user.addresses.set([address])

    # when
    limit_reached = is_user_address_limit_reached(customer_user)

    # then
    assert limit_reached is False


def test_store_user_address_uses_existing_one(address):
    """Ensure storing an address that is already associated to the given user doesn't
    create a new address, but uses the existing one instead.
    """
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.add(address)

    expected_user_addresses_count = 1

    manager = get_plugins_manager()
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id == address.pk


def test_store_user_address_uses_existing_one_despite_duplicated(address):
    """Ensure storing an address handles the possibility of an user
    having the same address associated to them multiple time is handled properly.

    It should use the first identical address associated to the user.
    """
    same_address = Address.objects.create(**address.as_data())
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.set([address, same_address])

    expected_user_addresses_count = 2

    manager = get_plugins_manager()
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id == address.pk


def test_store_user_address_create_new_address_if_not_associated(address):
    """Ensure storing an address that is not associated to the given user
    triggers the creation of a new address, but uses the existing one instead.
    """
    user = User.objects.create_user("test@example.com", "password")
    expected_user_addresses_count = 1

    manager = get_plugins_manager()
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id != address.pk


@override_settings(MAX_USER_ADDRESSES=2)
def test_store_user_address_address_not_saved(address):
    """Ensure that new address is not saved when user has already
    more than 100 addressess.
    """
    same_address = Address.objects.create(**address.as_data())
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.set([address, same_address])

    address_count = user.addresses.count()

    manager = get_plugins_manager()
    store_user_address(user, address, AddressType.BILLING, manager)

    assert user.addresses.count() == address_count


def test_remove_the_oldest_user_address(customer_user, address):
    """Ensure that oldest address that is not billing or shipping
    default address is removed."""
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
