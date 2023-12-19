from .. import models


def test_visible_to_customer_user(customer_user, published_collections, channel_USD):
    # given
    collection = published_collections[0]
    collection.channel_listings.all().delete()

    # when
    available_collections = models.Collection.objects.visible_to_user(
        customer_user, channel_USD.slug
    )

    # then
    assert available_collections.count() == len(published_collections) - 1


def test_visible_to_customer_user_without_channel_slug(
    customer_user,
    published_collections,
    channel_USD,
    django_assert_num_queries,
):
    # given
    collection = published_collections[0]
    collection.channel_listings.all().delete()

    # when
    available_collections = models.Collection.objects.visible_to_user(
        customer_user, None
    )

    # then
    with django_assert_num_queries(0):
        assert available_collections.count() == 0


def test_visible_to_staff_user(
    staff_user,
    published_collections,
    permission_manage_products,
    channel_USD,
):
    # given
    collection = published_collections[0]
    collection.channel_listings.all().delete()

    staff_user.user_permissions.add(permission_manage_products)

    # when
    available_collections = models.Collection.objects.visible_to_user(staff_user, None)

    # then
    assert available_collections.count() == len(published_collections)


def test_visible_to_staff_user_with_channel(
    staff_user,
    published_collections,
    permission_manage_products,
    channel_USD,
):
    # given
    collection = published_collections[0]
    collection.channel_listings.all().delete()

    staff_user.user_permissions.add(permission_manage_products)

    # when
    available_collections = models.Collection.objects.visible_to_user(
        staff_user, channel_USD.slug
    )

    # then
    assert available_collections.count() == len(published_collections) - 1
