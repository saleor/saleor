import pytest

from django.urls import reverse

from .utils import get_redirect_location


def test_collection_index(client, collection):
    url_kwargs = {'pk': collection.id, 'slug': collection.slug}
    url = reverse('product:collection', kwargs=url_kwargs)
    response = client.get(url)
    assert response.status_code == 200


def test_collection_incorrect_slug(client, collection):
    """When entered on the collection with proper PK but incorrect slug,
    one should be permanently(301) redirected to the proper url.
    """
    url_kwargs = {'pk': collection.id, 'slug': 'incorrect-slug'}
    url = reverse('product:collection', kwargs=url_kwargs)
    response = client.get(url)
    # User should be redirected to the proper url
    assert response.status_code == 301

    redirected_url = get_redirect_location(response)
    proper_kwargs = {'pk': collection.id, 'slug': collection.slug}
    proper_url = reverse('product:collection', kwargs=proper_kwargs)
    assert redirected_url == proper_url


def test_collection_not_exists(client):
    url_kwargs = {'pk': 123456, 'slug': 'incorrect-slug'}
    url = reverse('product:collection', kwargs=url_kwargs)
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.parametrize(
    'title, seo_title, expected_result',
    (
        ('Title', 'Seo Title', 'Seo Title'),
        ('Title', None, 'Title')))
def test_page_get_seo_title(
        admin_client, collection, title, seo_title, expected_result):
    collection.name = title
    collection.seo_title = seo_title
    collection.save()
    result = collection.get_seo_title()
    expected_result == result


@pytest.mark.parametrize(
    'seo_description, expected_result',
    (
        ('Seo', 'Seo'),
        (None, '')))
def test_page_get_seo_description(
        admin_client, collection, seo_description, expected_result):
    collection.seo_description = seo_description
    collection.save()
    result = collection.get_seo_description()
    expected_result == result
