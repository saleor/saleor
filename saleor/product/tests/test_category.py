from unittest.mock import patch

from ...plugins.manager import get_plugins_manager
from ..models import Category
from ..utils import collect_categories_tree_products, delete_categories


def test_collect_categories_tree_products(categories_tree):
    parent = categories_tree
    child = parent.children.first()
    products = parent.products.all() | child.products.all()

    result = collect_categories_tree_products(parent)

    assert len(result) == len(products)
    assert set(result.values_list("pk", flat=True)) == set(
        products.values_list("pk", flat=True)
    )


@patch("saleor.product.utils.update_products_discounted_prices_task")
def test_delete_categories(
    mock_update_products_discounted_prices_task,
    categories_tree_with_published_products,
):
    parent = categories_tree_with_published_products
    child = parent.children.first()
    product_list = [child.products.first(), parent.products.first()]

    delete_categories([parent.pk], manager=get_plugins_manager())

    assert not Category.objects.filter(
        id__in=[category.id for category in [parent, child]]
    ).exists()

    calls = mock_update_products_discounted_prices_task.mock_calls
    assert len(calls) == 1
    call_kwargs = calls[0].kwargs
    assert set(call_kwargs["product_ids"]) == {p.pk for p in product_list}

    for product in product_list:
        product.refresh_from_db()
        assert not product.category
        for product_channel_listing in product.channel_listings.all():
            assert not product_channel_listing.is_published
            assert not product_channel_listing.published_at


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_categories_trigger_product_updated_webhook(
    product_updated_mock,
    categories_tree_with_published_products,
):
    parent = categories_tree_with_published_products
    child = parent.children.first()
    product_list = [child.products.first(), parent.products.first()]

    delete_categories([parent.pk], manager=get_plugins_manager())

    assert not Category.objects.filter(
        id__in=[category.id for category in [parent, child]]
    ).exists()

    assert len(product_list) == product_updated_mock.call_count
