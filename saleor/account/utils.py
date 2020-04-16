import jwt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..account.error_codes import AccountErrorCode
from ..checkout import AddressType
from ..core.utils import create_thumbnails
from ..plugins.manager import get_plugins_manager
from .models import User


def store_user_address(user, address, address_type):
    """Add address to user address book and set as default one."""
    address = get_plugins_manager().change_user_address(address, address_type, user)
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


def set_user_default_billing_address(user, address):
    user.default_billing_address = address
    user.save(update_fields=["default_billing_address"])


def set_user_default_shipping_address(user, address):
    user.default_shipping_address = address
    user.save(update_fields=["default_shipping_address"])


def change_user_default_address(user, address, address_type):
    address = get_plugins_manager().change_user_address(address, address_type, user)
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
        create_thumbnails(
            pk=user.pk, model=User, size_set="user_avatars", image_attr="avatar"
        )
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


def create_jwt_token(token_data):
    expiration_date = timezone.now() + timezone.timedelta(hours=1)
    token_kwargs = {"exp": expiration_date}
    token_kwargs.update(token_data)
    token = jwt.encode(token_kwargs, settings.SECRET_KEY, algorithm="HS256").decode()
    return token


def decode_jwt_token(token):
    try:
        decoded_token = jwt.decode(
            token.encode(), settings.SECRET_KEY, algorithms=["HS256"]
        )
    except jwt.PyJWTError:
        raise ValidationError(
            {
                "token": ValidationError(
                    "Invalid or expired token.", code=AccountErrorCode.INVALID
                )
            }
        )
    return decoded_token
