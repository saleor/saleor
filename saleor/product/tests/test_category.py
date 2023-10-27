from unittest.mock import patch

from ...plugins.manager import get_plugins_manager
from ...tests.utils import flush_post_commit_hooks
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


@patch("saleor.product.utils.get_webhooks_for_event")
@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_categories_trigger_product_updated_webhook(
    product_updated_mock,
    mocked_get_webhooks_for_event,
    categories_tree_with_published_products,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    parent = categories_tree_with_published_products
    child = parent.children.first()
    product_list = [child.products.first(), parent.products.first()]

    # when
    delete_categories([parent.pk], manager=get_plugins_manager())
    flush_post_commit_hooks()

    # then
    assert not Category.objects.filter(
        id__in=[category.id for category in [parent, child]]
    ).exists()

    assert len(product_list) == product_updated_mock.call_count
