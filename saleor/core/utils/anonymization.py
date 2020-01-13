import copy
from typing import TYPE_CHECKING

from faker import Faker

from ...account.models import Address, User

if TYPE_CHECKING:
    from ...order.models import Order
    from ...checkout.models import Checkout

fake = Faker()


def generate_fake_address() -> "Address":
    return Address(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        company_name=fake.company(),
        street_address_1=fake.street_address(),
        street_address_2=fake.secondary_address(),
        city=fake.city(),
        postal_code=fake.postalcode(),
        country=fake.country(),
        phone=fake.phone_number(),
    )


def generate_fake_user() -> "User":
    return User(
        email=fake.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        is_active=True,
        note=fake.paragraph(),
        date_joined=fake.date_time(),
        default_shipping_address=generate_fake_address(),
        default_billing_address=generate_fake_address(),
        meta=fake.pystruct(count=1),
        private_meta=fake.pystruct(count=1),
    )


def anonymize_order(order: "Order"):
    anonymized_order = copy.deepcopy(order)
    # Prevent accidental savings of the instance
    anonymized_order.pk = -1
    fake_user = generate_fake_user()
    anonymized_order.user = fake_user
    anonymized_order.user_email = fake_user.email
    anonymized_order.shipping_address = generate_fake_address()
    anonymized_order.billing_address = generate_fake_address()
    anonymized_order.customer_note = fake.paragraph()
    anonymized_order.meta = fake.pystruct(count=1)
    anonymized_order.private_meta = fake.pystruct(count=1)
    return anonymized_order


def anonymize_checkout(checkout: "Checkout"):
    anonymized_checkout = copy.deepcopy(checkout)
    # Prevent accidental savings of the instance
    anonymized_checkout.token = ""  # Token is the "pk" for checkout
    fake_user = generate_fake_user()
    anonymized_checkout.user = fake_user
    anonymized_checkout.email = fake_user.email
    anonymized_checkout.shipping_address = generate_fake_address()
    anonymized_checkout.billing_address = generate_fake_address()
    anonymized_checkout.note = fake.paragraph()
    anonymized_checkout.meta = fake.pystruct(count=1)
    anonymized_checkout.private_meta = fake.pystruct(count=1)
    return anonymized_checkout
