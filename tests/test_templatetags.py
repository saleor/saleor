from django.template import Context, Template
from django.urls import reverse

from saleor.core.context_processors import navigation
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


def test_menu_rendering(client, menu_with_items, collection):
    collection.is_published = False
    collection.save()
    context_dict = navigation(None)
    context_dict.update({'menu': menu_with_items})
    template = Template(
        '{% load shop %} {% menu site_menu=menu horizontal=True %}')
    context = Context(context_dict)
    rendered_menu = template.render(context)
    for item in menu_with_items.items.all():
        if item.collection == collection:
            assert item.get_url() not in rendered_menu
        else:
            assert item.get_url() in rendered_menu
