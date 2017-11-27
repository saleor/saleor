from __future__ import unicode_literals

import json

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


def test_ajax_users_list_get_all_users(admin_client, customer_user):
    url = reverse('dashboard:ajax-users-list')
    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    resp_decoded = json.loads(response.content.decode('utf-8'))
    results = resp_decoded['results']
    assert len(results) == 2


def test_ajax_users_list_filter_users(admin_client, customer_user):
    url = '%s?q=%s' % (
        reverse('dashboard:ajax-users-list'), customer_user.email)
    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    resp_decoded = json.loads(response.content.decode('utf-8'))
    results = resp_decoded['results']
    label = '%s (%s)' % (customer_user.full_name, customer_user.email)
    assert len(results) == 1
    assert results[0]['id'] == customer_user.pk
    assert results[0]['text'] == label
