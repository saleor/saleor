import pytest
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from saleor.account.models import User


def test_staff_with_permission_can_impersonate(
        staff_client, customer_user, staff_user, permission_impersonate_users):
    staff_user.user_permissions.add(permission_impersonate_users)
    staff_user = User.objects.get(pk=staff_user.pk)
    response = staff_client.get(reverse('impersonate-start',
                                args=[customer_user.pk]), follow=True)
    assert response.context['user'] == customer_user
    assert response.context['user'].is_impersonate
    assert response.context['request'].impersonator == staff_user

    response = staff_client.get(reverse('impersonate-stop'), follow=True)
    assert response.context['user'] == staff_user
    assert response.context['user'].is_impersonate is False


def test_impersonate_list_search_urls_are_disabled():
    with pytest.raises(NoReverseMatch):
        reverse('impersonate-list')
    with pytest.raises(NoReverseMatch):
        reverse('impersonate-search')


def test_impersonate_start_url_uid_arg_is_number():
    with pytest.raises(NoReverseMatch):
        reverse('impersonate', args=['string'])
