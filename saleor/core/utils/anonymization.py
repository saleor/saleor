import copy
import datetime
import logging
import unicodedata
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connection
from faker import Faker

from ...account.models import Address, User
from ...checkout.utils import get_or_create_checkout_metadata

if TYPE_CHECKING:
    from ...checkout.models import Checkout
    from ...order.models import Order

logger = logging.getLogger(__name__)

fake = Faker()


def _fake_save(*args, **kwargs):
    logger.error("Unable to save fake instance")


def get_email(first_name, last_name):
    _first = unicodedata.normalize("NFD", first_name).encode("ascii", "ignore")
    _last = unicodedata.normalize("NFD", last_name).encode("ascii", "ignore")
    decoded_first = _first.lower().decode("utf-8")
    decoded_last = _last.lower().decode("utf-8")
    return f"{decoded_first}.{decoded_last}@example.com"


def generate_fake_address(*, with_fake_save: bool = True, **kwargs) -> Address:
    """Generate a fake instance of the "Address" class.

    The instance cannot be saved
    """

    address = Address(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        street_address_1=fake.street_address(),
        city=fake.city(),
        country=settings.DEFAULT_COUNTRY,
        **kwargs,
    )

    if address.country == "US":
        state = fake.state_abbr(include_territories=False)
        address.country_area = state
        address.postal_code = fake.postalcode_in_state(state)
    else:
        address.postal_code = fake.postalcode()

    # Prevent accidental saving of the instance
    if with_fake_save:
        address.save = _fake_save  # type: ignore[method-assign]
    return address


def generate_fake_user(
    *, with_fake_save: bool = True, generate_id: bool = True
) -> tuple[User, Address]:
    """Generate a fake instance of the "User" class.

    The instance cannot be saved
    """

    # def create_fake_user(user_password, save=True, generate_id=False, customer_type=None):
    address = generate_fake_address(with_fake_save=with_fake_save)
    email = get_email(address.first_name, address.last_name)

    user_params = {
        "first_name": address.first_name,
        "last_name": address.last_name,
        "email": email,
        "default_billing_address": address,
        "default_shipping_address": address,
        "is_active": True,
        "note": fake.paragraph(),
        "date_joined": fake.date_time(tzinfo=datetime.UTC),
    }

    if generate_id:
        _, max_user_id = connection.ops.integer_field_range(
            User.id.field.get_internal_type()
        )
        user_params["id"] = fake.random_int(min=1, max=max_user_id)

    fake_user = User(**user_params)
    fake_user.set_unusable_password()

    # Prevent accidental saving of the instance
    if with_fake_save:
        fake_user.save = _fake_save  # type: ignore[method-assign]
    return fake_user, address


def generate_fake_metadata() -> dict[str, str]:
    """Generate a fake metadata/private metadata dictionary."""
    return fake.pydict(value_types=[str])


def anonymize_order(order: "Order") -> "Order":
    """Generate an anonymized version of the provided order.

    The instance cannot be saved
    """
    anonymized_order = copy.deepcopy(order)
    # Prevent accidental saving of the instance
    anonymized_order.save = _fake_save  # type: ignore[method-assign]
    fake_user, _fake_address = generate_fake_user()
    anonymized_order.user = fake_user
    anonymized_order.user_email = fake_user.email
    anonymized_order.shipping_address = generate_fake_address()
    anonymized_order.billing_address = generate_fake_address()
    anonymized_order.customer_note = fake.paragraph()
    anonymized_order.metadata = generate_fake_metadata()
    anonymized_order.private_metadata = generate_fake_metadata()
    return anonymized_order


def anonymize_checkout(checkout: "Checkout") -> "Checkout":
    """Generate an anonymized version of the provided checkout.

    The instance cannot be saved
    """
    anonymized_checkout = copy.deepcopy(checkout)
    # Prevent accidental saving of the instance
    anonymized_checkout.save = _fake_save  # type: ignore[method-assign]
    fake_user, _fake_address = generate_fake_user()
    anonymized_checkout.user = fake_user
    anonymized_checkout.email = fake_user.email
    anonymized_checkout.shipping_address = generate_fake_address()
    anonymized_checkout.billing_address = generate_fake_address()
    anonymized_checkout.note = fake.paragraph()
    anonymized_checkout_metadata = get_or_create_checkout_metadata(anonymized_checkout)
    anonymized_checkout_metadata.metadata = generate_fake_metadata()
    anonymized_checkout_metadata.private_metadata = generate_fake_metadata()
    return anonymized_checkout
