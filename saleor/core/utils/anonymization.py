import copy
import logging
from typing import TYPE_CHECKING

from faker import Faker

from ...account.models import Address, User
from .random_data import create_address, create_fake_user

if TYPE_CHECKING:
    from ...checkout.models import Checkout
    from ...order.models import Order

logger = logging.getLogger(__name__)

fake = Faker()


def _fake_save(*args, **kwargs):
    logger.error("Unable to save fake instance")


def generate_fake_address() -> "Address":
    """Generate a fake instance of the "Address" class.

    The instance cannot be saved
    """
    fake_address = create_address(save=False)
    # Prevent accidental saving of the instance
    fake_address.save = _fake_save  # type: ignore
    return fake_address


def generate_fake_user() -> "User":
    """Generate a fake instance of the "User" class.

    The instance cannot be saved
    """
    fake_user = create_fake_user(save=False)
    # Prevent accidental saving of the instance
    fake_user.save = _fake_save  # type: ignore
    return fake_user


def anonymize_order(order: "Order") -> "Order":
    """Generate an anonymized version of the provided order.

    The instance cannot be saved
    """
    anonymized_order = copy.deepcopy(order)
    # Prevent accidental saving of the instance
    anonymized_order.save = _fake_save  # type: ignore
    fake_user = generate_fake_user()
    anonymized_order.user = fake_user
    anonymized_order.user_email = fake_user.email
    anonymized_order.shipping_address = generate_fake_address()
    anonymized_order.billing_address = generate_fake_address()
    anonymized_order.customer_note = fake.paragraph()
    anonymized_order.metadata = fake.pystruct(count=1)
    anonymized_order.private_metadata = fake.pystruct(count=1)
    return anonymized_order


def anonymize_checkout(checkout: "Checkout") -> "Checkout":
    """Generate an anonymized version of the provided checkout.

    The instance cannot be saved
    """
    anonymized_checkout = copy.deepcopy(checkout)
    # Prevent accidental saving of the instance
    anonymized_checkout.token = ""  # Token is the "pk" for checkout
    anonymized_checkout.save = _fake_save  # type: ignore
    fake_user = generate_fake_user()
    anonymized_checkout.user = fake_user
    anonymized_checkout.email = fake_user.email
    anonymized_checkout.shipping_address = generate_fake_address()
    anonymized_checkout.billing_address = generate_fake_address()
    anonymized_checkout.note = fake.paragraph()
    anonymized_checkout.metadata = fake.pystruct(count=1)
    anonymized_checkout.private_metadata = fake.pystruct(count=1)
    return anonymized_checkout
