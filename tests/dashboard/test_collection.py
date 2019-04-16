import json
from unittest import mock
from unittest.mock import Mock

from django.urls import reverse

from saleor.dashboard.collection.forms import CollectionForm
from saleor.product.models import Collection

from ..utils import create_image, get_redirect_location


def test_list_view(admin_client, collection):
    response = admin_client.get(reverse('dashboard:collection-list'))
    assert response.status_code == 200
    context = response.context
    assert list(context['collections']) == [collection]


def test_set_homepage_collection(admin_client, collection, site_settings):
    data = {'homepage_collection': collection.pk}
    response = admin_client.post(reverse('dashboard:collection-list'), data)
    assert response.status_code == 302
    redirect_url = reverse('dashboard:collection-list')
    assert get_redirect_location(response) == redirect_url
    site_settings.refresh_from_db()
    assert site_settings.homepage_collection == collection


def test_set_unpublished_homepage_collection(
        admin_client, collection, site_settings):
    collection.is_published = False
    collection.save()
    data = {'homepage_collection': collection.pk}
    response = admin_client.post(reverse('dashboard:collection-list'), data)
    assert response.status_code == 200
    site_settings.refresh_from_db()
    assert site_settings.homepage_collection is None
    assert not response.context['assign_homepage_col_form'].is_valid()


def test_collection_form_name():
    data = {'name': 'Test Collection', 'products': []}
    form = CollectionForm(data)
    assert form.is_valid()

    collection = form.save()
    assert collection.slug == 'test-collection'

    invalid_form = CollectionForm()
    assert not invalid_form.is_valid()


def test_collection_form_with_products(product):
    data = {'name': 'Test collection', 'products': [product.id]}
    form = CollectionForm(data)
    assert form.is_valid()

    collection = form.save()
    assert collection.products.count() == 1


def test_collection_create_view(monkeypatch, admin_client):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    response = admin_client.get(reverse('dashboard:collection-add'))
    assert response.status_code == 200

    data = {'name': 'Test'}
    response = admin_client.post(reverse('dashboard:collection-add'), data)
    assert response.status_code == 302

    redirected_url = get_redirect_location(response)
    assert redirected_url == reverse('dashboard:collection-list')
    assert mock_create_thumbnails.call_count == 0


def test_collection_create_with_background_image(
        monkeypatch, admin_client, media_root):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    image, image_name = create_image()

    data = {
        'name': 'Name',
        'background_image': image}
    url = reverse('dashboard:collection-add')

    response = admin_client.post(url, data)
    assert response.status_code == 302
    mock_create_thumbnails.assert_called_once_with(
        Collection.objects.last().pk)


def test_collection_update_view(
        monkeypatch, admin_client, collection, product):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    url = reverse('dashboard:collection-update', kwargs={'pk': collection.id})
    response = admin_client.get(url)
    assert response.status_code == 200

    current_name = collection.name
    data = {'name': 'New name', 'products': [product.id]}
    response = admin_client.post(url, data)
    assert response.status_code == 302

    collection.refresh_from_db()
    assert not current_name == collection.name
    assert list(collection.products.all()) == [product]

    assert mock_create_thumbnails.call_count == 0


def test_collection_update_background_image(
        monkeypatch, admin_client, collection, product, media_root):
    mock_create_category_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_category_thumbnails)

    url = reverse('dashboard:collection-update', kwargs={'pk': collection.id})
    image, image_name = create_image()

    data = {
        'name': 'New name',
        'background_image': image}
    response = admin_client.post(url, data)
    assert response.status_code == 302

    collection.refresh_from_db()
    assert collection.background_image
    assert image_name in collection.background_image.name

    mock_create_category_thumbnails.assert_called_once_with(collection.pk)


@mock.patch('saleor.dashboard.collection.views.get_menus_that_needs_update')
@mock.patch('saleor.dashboard.collection.views.update_menus')
def test_collection_delete_view(
        mock_update_menus, mock_get_menus, admin_client, collection):
    # Test Http404 when collection doesn't exist
    url404 = reverse('dashboard:collection-delete', kwargs={'pk': 123123})
    response404 = admin_client.post(url404)
    assert response404.status_code == 404

    # Test deleting object
    collections_count = Collection.objects.count()
    url = reverse('dashboard:collection-delete', kwargs={'pk': collection.id})
    mock_get_menus.return_value = [collection.id]
    response = admin_client.post(url)
    assert response.status_code == 302
    mock_update_menus.assert_called_once_with([collection.pk])

    assert Collection.objects.count() == (collections_count - 1)


@mock.patch('saleor.dashboard.collection.views.get_menus_that_needs_update')
@mock.patch('saleor.dashboard.collection.views.update_menus')
def test_collection_delete_view_menus_not_updated(
        mock_update_menus, mock_get_menus, admin_client, collection):
    url = reverse('dashboard:collection-delete', kwargs={'pk': collection.id})
    mock_get_menus.return_value = []
    response = admin_client.post(url)
    assert response.status_code == 302
    assert mock_get_menus.called
    assert not mock_update_menus.called


def test_collection_is_published_toggle_view(db, admin_client, collection):
    url = reverse('dashboard:collection-publish', kwargs={'pk': collection.pk})
    response = admin_client.post(url)
    assert response.status_code == 200
    data = {'success': True, 'is_published': False}
    assert json.loads(response.content.decode('utf8')) == data
    admin_client.post(url)
    collection.refresh_from_db()
    assert collection.is_published
