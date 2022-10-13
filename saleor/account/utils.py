from typing import TYPE_CHECKING

from django.conf import settings

from ..checkout import AddressType
from .models import User

if TYPE_CHECKING:
    from ..plugins.manager import PluginsManager
    from .models import Address


def store_user_address(
    user: User,
    address: "Address",
    address_type: str,
    manager: "PluginsManager",
):
    """Add address to user address book and set as default one."""

    # user can only have specified number of addresses
    # so we do not want to store additional one if user already reached the max
    # number of addresses
    if is_user_address_limit_reached(user):
        return

    address = manager.change_user_address(address, address_type, user)
    address_data = address.as_data()

    address = user.addresses.filter(**address_data).first()
    if address is None:
        address = user.addresses.create(**address_data)

    if address_type == AddressType.BILLING:
        if not user.default_billing_address:
            set_user_default_billing_address(user, address)
    elif address_type == AddressType.SHIPPING:
        if not user.default_shipping_address:
            set_user_default_shipping_address(user, address)


def is_user_address_limit_reached(user: "User"):
    """Return True if user cannot have more addresses."""
    return user.addresses.count() >= settings.MAX_USER_ADDRESSES


def remove_the_oldest_user_address_if_address_limit_is_reached(user: "User"):
    """Remove the oldest user address when max address limit is reached."""
    if is_user_address_limit_reached(user):
        remove_the_oldest_user_address(user)


def remove_the_oldest_user_address(user: "User"):
    user_default_addresses_ids = [
        user.default_billing_address_id,
        user.default_shipping_address_id,
    ]
    user_address = (
        user.addresses.exclude(pk__in=user_default_addresses_ids).order_by("pk").first()
    )
    if user_address:
        user_address.delete()


def set_user_default_billing_address(user, address):
    user.default_billing_address = address
    user.save(update_fields=["default_billing_address", "updated_at"])


def set_user_default_shipping_address(user, address):
    user.default_shipping_address = address
    user.save(update_fields=["default_shipping_address", "updated_at"])


def change_user_default_address(
    user: User, address: "Address", address_type: str, manager: "PluginsManager"
):
    address = manager.change_user_address(address, address_type, user)
    if address_type == AddressType.BILLING:
        if user.default_billing_address:
            user.addresses.add(user.default_billing_address)
        set_user_default_billing_address(user, address)
    elif address_type == AddressType.SHIPPING:
        if user.default_shipping_address:
            user.addresses.add(user.default_shipping_address)
        set_user_default_shipping_address(user, address)


def create_superuser(credentials):

    user, created = User.objects.get_or_create(
        email=credentials["email"],
        defaults={"is_active": True, "is_staff": True, "is_superuser": True},
    )
    if created:
        user.set_password(credentials["password"])
        user.save()
        msg = "Superuser - %(email)s/%(password)s" % credentials
    else:
        msg = "Superuser already exists - %(email)s" % credentials
    return msg


def remove_staff_member(staff):
    """Remove staff member account only if it has no orders placed.

    Otherwise, switches is_staff status to False.
    """
    if staff.orders.exists():
        staff.is_staff = False
        staff.user_permissions.clear()
        staff.save()
    else:
        staff.delete()
