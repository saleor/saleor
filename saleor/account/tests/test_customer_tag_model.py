import pytest
from django.db.utils import IntegrityError

from ..models import CustomerTag, UserCustomerTag


def test_customer_tag_slug_is_unique(customer_tag):
    # when / then
    with pytest.raises(IntegrityError):
        CustomerTag.objects.create(name="Other", slug=customer_tag.slug)


def test_user_customer_tag_assignment_is_unique(customer_user, customer_tag):
    # given
    UserCustomerTag.objects.create(user=customer_user, tag=customer_tag)

    # when / then
    with pytest.raises(IntegrityError):
        UserCustomerTag.objects.create(user=customer_user, tag=customer_tag)


def test_user_tags_relation(customer_user, customer_tag):
    # when
    customer_user.tags.add(customer_tag)

    # then
    assert list(customer_user.tags.all()) == [customer_tag]
    assert list(customer_tag.users.all()) == [customer_user]
