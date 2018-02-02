from django.urls import reverse

from saleor.core.templatetags.shop import get_sort_by_url


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
