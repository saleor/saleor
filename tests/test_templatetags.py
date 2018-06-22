from django.urls import reverse

from saleor.core.templatetags.shop import get_sort_by_url, menu


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


def test_menu(client, menu_with_items):
    response = client.get(reverse('home'))
    result = menu(response.context, menu_with_items)
    assert all((i for i in result['menu_items'] if i.parent_id is None))
