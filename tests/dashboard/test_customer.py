from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from saleor.userprofile.models import User


def test_customer_promote_to_staff_with_POST(admin_client, customer_user):
    assert User.objects.filter(is_staff=True).count() == 1
    url = reverse(
        'dashboard:customer-promote', kwargs={'pk': customer_user.pk})
    admin_client.get(url)
    assert User.objects.filter(is_staff=True).count() == 1


def test_customer_promote_to_staff(admin_client, customer_user):
    assert User.objects.filter(is_staff=True).count() == 1
    url = reverse(
        'dashboard:customer-promote', kwargs={'pk': customer_user.pk})
    data = {'pk': customer_user.pk}
    response = admin_client.post(url, data)
    assert User.objects.filter(is_staff=True).count() == 2
    assert response['Location'] == reverse('dashboard:customer-details',
                                           kwargs={'pk': customer_user.pk})
