import pytest

from django.urls import reverse

from saleor.core.templatetags.shop import get_sort_by_url
from saleor.dashboard.templatetags.utils import render_sorting_header


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


def test_render_sorting_header_prepare_initial_data(admin_client):
    url = reverse('dashboard:product-list')
    response = admin_client.get(url)
    result = render_sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=name'
    assert result['is_active'] == False
    assert result['sorting_icon'] == ''


def test_render_sorting_header_name_field(admin_client):
    url = reverse('dashboard:product-list')
    data = {'sort_by': 'name'}
    response = admin_client.get(url, data)
    result = render_sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=-name'
    assert result['is_active'] == True

    data = {'sort_by': '-name'}
    response = admin_client.get(url, data)
    result = render_sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=name'
    assert result['is_active'] == True


def test_render_sorting_header_many_fields(admin_client):
    url = reverse('dashboard:product-list')
    data = {'sort_by': 'name'}
    response = admin_client.get(url, data)
    result = render_sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=-name'
    assert result['is_active'] == True

    data = {'sort_by': 'price'}
    response = admin_client.get(url, data)
    result = render_sorting_header(response.context, 'price', 'Price')
    assert result['url'] == url + '?sort_by=-price'
    assert result['is_active'] == True
