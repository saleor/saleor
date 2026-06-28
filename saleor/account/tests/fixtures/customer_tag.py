import pytest

from ....account.models import CustomerTag, UserCustomerTag


@pytest.fixture
def customer_tag():
    return CustomerTag.objects.create(
        name="VIP",
        slug="vip",
        description="High-value customers.",
        is_public=True,
    )


@pytest.fixture
def customer_tags():
    return CustomerTag.objects.bulk_create(
        [
            CustomerTag(name="VIP", slug="vip", is_public=True),
            CustomerTag(name="Wholesale", slug="wholesale", is_public=False),
            CustomerTag(name="Employee", slug="employee", is_public=False),
        ]
    )


@pytest.fixture
def customer_user_with_tag(customer_user, customer_tag):
    UserCustomerTag.objects.create(user=customer_user, tag=customer_tag)
    return customer_user
