import pytest

from ...fetch import fetch_checkout_lines


@pytest.fixture
def checkout_lines_info(checkout_with_items, categories, published_collections):
    lines = checkout_with_items.lines.all()
    category1, category2 = categories

    product1 = lines[0].variant.product
    product1.category = category1
    product1.collections.add(*published_collections[:2])
    product1.save()

    product2 = lines[1].variant.product
    product2.category = category2
    product2.collections.add(published_collections[0])
    product2.save()

    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    return lines_info


@pytest.fixture
def checkout_lines_with_multiple_quantity_info(
    checkout_with_items, categories, published_collections
):
    checkout_with_items.lines.update(quantity=5)
    lines = checkout_with_items.lines.all()
    category1, category2 = categories

    product1 = lines[0].variant.product
    product1.category = category1
    product1.collections.add(*published_collections[:2])
    product1.save()

    product2 = lines[1].variant.product
    product2.category = category2
    product2.collections.add(published_collections[0])
    product2.save()

    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    return lines_info
