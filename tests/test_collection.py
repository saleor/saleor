from datetime import date, timedelta

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


def test_collection_not_yet_published_returns_404(
        admin_client, client, draft_collection):
    url_kwargs = {'pk': draft_collection.pk, 'slug': draft_collection.slug}
    url = reverse('product:collection', kwargs=url_kwargs)
    response = client.get(url)
    assert response.status_code == 404

    draft_collection.is_published = True
    draft_collection.publication_date = date.today() + timedelta(days=1)
    draft_collection.save()

    # A non staff user should not have access to collections yet to be published
    response = client.get(url)
    assert response.status_code == 404

    # A staff user should have access to collections yet to be published
    response = admin_client.get(url)
    assert response.status_code == 200
