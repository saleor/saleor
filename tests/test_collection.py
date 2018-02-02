import pytest

from django.urls import reverse

from .utils import get_redirect_location
from saleor.dashboard.collection.forms import CollectionForm
from saleor.product.models import Collection


@pytest.fixture
def collection(db):
    collection = Collection.objects.create(
        name="Collection", slug='collection')
    return collection


def test_list_view(admin_client, collection):
    response = admin_client.get(reverse('dashboard:collection-list'))
    assert response.status_code == 200
    context = response.context
    assert list(context['collections']) == [collection]


@pytest.mark.django_db
def test_collection_form_name():
    data = {'name': 'Test Collection', 'products': []}
    form = CollectionForm(data)
    assert form.is_valid()

    collection = form.save()
    assert collection.slug == 'test-collection'

    invalid_form = CollectionForm()
    assert not invalid_form.is_valid()


@pytest.mark.django_db
def test_collection_form_with_products(product_in_stock):
    data = {'name': 'Test collection',
            'products': [product_in_stock.id]}
    form = CollectionForm(data)
    assert form.is_valid()

    collection = form.save()
    assert collection.products.count() == 1


def test_collection_create_view(admin_client):
    response = admin_client.get(reverse('dashboard:collection-add'))
    assert response.status_code == 200

    data = {'name': 'Test'}
    response = admin_client.post(reverse('dashboard:collection-add'), data)
    assert response.status_code == 302

    redirected_url = get_redirect_location(response)
    assert redirected_url == reverse('dashboard:collection-list')


def test_collection_update_view(admin_client, collection, product_in_stock):
    url = reverse('dashboard:collection-update',
                  kwargs={'pk': collection.id})
    response = admin_client.get(url)
    assert response.status_code == 200

    current_name = collection.name
    data = {'name': 'New name', 'products': [product_in_stock.id]}
    response = admin_client.post(url, data)
    assert response.status_code == 302

    collection.refresh_from_db()
    assert not current_name == collection.name
    assert list(collection.products.all()) == [product_in_stock]


def test_collection_delete_view(admin_client, collection):
    # Test Http404 when collection doesn't exist
    pk = 500
    url404 = reverse('dashboard:collection-delete',
                     kwargs={'pk': pk})
    response404 = admin_client.post(url404)
    assert response404.status_code == 404

    # Test deleting object
    collections_count = Collection.objects.count()
    url = reverse('dashboard:collection-delete',
                  kwargs={'pk': collection.id})
    response = admin_client.post(url)
    assert response.status_code == 302
    assert Collection.objects.count() == (collections_count - 1)


def test_collection_index_in_storefront(admin_client, collection):
    response = admin_client.get(
        reverse(
            'product:collection', kwargs={
                'pk': collection.id, 'slug': collection.slug}))
    assert response.status_code == 200
