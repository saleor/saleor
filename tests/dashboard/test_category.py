from django.urls import reverse

from saleor.product.models import Category


def test_category_list(admin_client, default_category):
    url = reverse('dashboard:category-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_category_add(admin_client):
    assert Category.objects.count() == 0
    url = reverse('dashboard:category-add')
    data = {'name': 'Cars', 'description': 'Fastest cars'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 1


def test_category_add_not_valid(admin_client):
    assert Category.objects.count() == 0
    url = reverse('dashboard:category-add')
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 0


def test_category_add_subcategory(admin_client, default_category):
    assert Category.objects.count() == 1
    url = reverse('dashboard:category-add',
                  kwargs={'root_pk': default_category.pk})
    data = {'name': 'Cars', 'description': 'Fastest cars'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 2
    default_category.refresh_from_db()
    subcategories = default_category.get_children()
    assert len(subcategories) == 1
    assert subcategories[0].name == 'Cars'


def test_category_edit(admin_client, default_category):
    assert Category.objects.count() == 1
    url = reverse('dashboard:category-edit',
                  kwargs={'root_pk': default_category.pk})
    data = {'name': 'Cars', 'description': 'Super fast!'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 1
    assert Category.objects.all()[0].name == 'Cars'


def test_category_details(admin_client, default_category):
    assert Category.objects.count() == 1
    url = reverse('dashboard:category-details',
                  kwargs={'pk': default_category.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200


def test_category_delete(admin_client, default_category):
    assert Category.objects.count() == 1
    url = reverse('dashboard:category-delete',
                  kwargs={'pk': default_category.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 0
