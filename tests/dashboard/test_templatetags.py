import pytest

from django.urls import reverse

from saleor.core.templatetags.shop import get_sort_by_url, get_sort_by_toggle


def test_sort_by_url_ascending(admin_client, default_category):
    url = reverse('product:category',
                  kwargs={'path': default_category.slug,
                          'category_id': default_category.id})
    response = admin_client.get(url)
    result = get_sort_by_url(response.context, 'name')
    expected = url + '?sort_by=name'
    assert result == expected


def test_sort_by_url_descending(admin_client, default_category):
    url = reverse('product:category',
                  kwargs={'path': default_category.slug,
                          'category_id': default_category.id})
    response = admin_client.get(url)
    result = get_sort_by_url(response.context, 'name', descending=True)
    expected = url + '?sort_by=-name'
    assert result == expected


def test_sort_by_toggle_prepare_initial_data(admin_client):
    url = reverse('dashboard:product-list')
    response = admin_client.get(url)
    result = get_sort_by_toggle(response.context, 'name')
    assert result['url'] == url + '?sort_by=name'
    assert result['is_active'] == False
    assert result['sorting_icon'] == ''


def test_sort_by_toggle_name_field(admin_client):
    url = reverse('dashboard:product-list')
    data = {'sort_by': 'name'}
    response = admin_client.get(url, data)
    result = get_sort_by_toggle(response.context, 'name')
    assert result['url'] == url + '?sort_by=-name'
    assert result['is_active'] == True

    data = {'sort_by': '-name'}
    response = admin_client.get(url, data)
    result = get_sort_by_toggle(response.context, 'name')
    assert result['url'] == url + '?sort_by=name'
    assert result['is_active'] == True


def test_sort_by_toggle_many_fields(admin_client):
    url = reverse('dashboard:product-list')
    data = {'sort_by': 'name'}
    response = admin_client.get(url, data)
    result = get_sort_by_toggle(response.context, 'name')
    assert result['url'] == url + '?sort_by=-name'
    assert result['is_active'] == True

    data = {'sort_by': 'price'}
    response = admin_client.get(url, data)
    result = get_sort_by_toggle(response.context, 'price')
    assert result['url'] == url + '?sort_by=-price'
    assert result['is_active'] == True
