import datetime

import pytest
from django.utils import timezone

from ....tests.utils import dummy_editorjs
from ...models import Collection, CollectionChannelListing


@pytest.fixture
def collection(db):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description=dummy_editorjs("Test description."),
    )
    return collection


@pytest.fixture
def published_collection(db, channel_USD):
    collection = Collection.objects.create(
        name="Collection USD",
        slug="collection-usd",
        description=dummy_editorjs("Test description."),
    )
    CollectionChannelListing.objects.create(
        channel=channel_USD,
        collection=collection,
        is_published=True,
        published_at=timezone.now(),
    )
    return collection


@pytest.fixture
def published_collections(db, channel_USD):
    collections = Collection.objects.bulk_create(
        [
            Collection(
                name="Collection1",
                slug="coll1",
            ),
            Collection(
                name="Collection2",
                slug="coll2",
            ),
            Collection(
                name="Collection3",
                slug="coll3",
            ),
        ]
    )
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD,
                collection=collection,
                is_published=True,
                published_at=datetime.datetime(2019, 4, 10, tzinfo=datetime.UTC),
            )
            for collection in collections
        ]
    )

    return collections


@pytest.fixture
def published_collection_PLN(db, channel_PLN):
    collection = Collection.objects.create(
        name="Collection PLN",
        slug="collection-pln",
        description=dummy_editorjs("Test description."),
    )
    CollectionChannelListing.objects.create(
        channel=channel_PLN,
        collection=collection,
        is_published=True,
        published_at=timezone.now(),
    )
    return collection


@pytest.fixture
def unpublished_collection(db, channel_USD):
    collection = Collection.objects.create(
        name="Unpublished Collection",
        slug="unpublished-collection",
        description=dummy_editorjs("Test description."),
    )
    CollectionChannelListing.objects.create(
        channel=channel_USD, collection=collection, is_published=False
    )
    return collection


@pytest.fixture
def unpublished_collection_PLN(db, channel_PLN):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description=dummy_editorjs("Test description."),
    )
    CollectionChannelListing.objects.create(
        channel=channel_PLN, collection=collection, is_published=False
    )
    return collection


@pytest.fixture
def collection_with_products(db, published_collection, product_list_published):
    published_collection.products.set(list(product_list_published))
    return product_list_published


@pytest.fixture
def collection_with_image(db, image, media_root, channel_USD):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description=dummy_editorjs("Test description."),
        background_image=image,
    )
    CollectionChannelListing.objects.create(
        channel=channel_USD, collection=collection, is_published=False
    )
    return collection


@pytest.fixture
def collection_list(db, channel_USD):
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Collection 1", slug="collection-1"),
            Collection(name="Collection 2", slug="collection-2"),
            Collection(name="Collection 3", slug="collection-3"),
        ]
    )
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD, collection=collection, is_published=True
            )
            for collection in collections
        ]
    )
    return collections
