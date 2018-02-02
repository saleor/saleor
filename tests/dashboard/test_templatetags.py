from django.urls import reverse

from saleor.dashboard.templatetags.utils import sorting_header


def test_sorting_header_prepare_initial_data(admin_client):
    url = reverse('dashboard:product-list')
    response = admin_client.get(url)
    result = sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=name'
    assert result['is_active'] is False
    assert result['sorting_icon'] == ''


def test_sorting_header_name_field(admin_client):
    url = reverse('dashboard:product-list')
    data = {'sort_by': 'name'}
    response = admin_client.get(url, data)
    result = sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=-name'
    assert result['is_active'] is True

    data = {'sort_by': '-name'}
    response = admin_client.get(url, data)
    result = sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=name'
    assert result['is_active'] is True


def test_sorting_header_many_fields(admin_client):
    url = reverse('dashboard:product-list')
    data = {'sort_by': 'name'}
    response = admin_client.get(url, data)
    result = sorting_header(response.context, 'name', 'Name')
    assert result['url'] == url + '?sort_by=-name'
    assert result['is_active'] is True

    data = {'sort_by': 'price'}
    response = admin_client.get(url, data)
    result = sorting_header(response.context, 'price', 'Price')
    assert result['url'] == url + '?sort_by=-price'
    assert result['is_active'] is True
