import json

import pytest

from saleor.seo.schema.email import (
    get_order_confirmation_markup, get_organization, get_product_data)


def test_get_organization(site_settings):
    example_name = 'Saleor Brand Name'
    site = site_settings.site
    site.name = example_name
    site.save()

    result = get_organization()
    assert result['name'] == example_name


def test_get_product_data_without_image(order_with_lines_and_stock):
    """Tested OrderLine Product has no image assigned."""
    order_line = order_with_lines_and_stock.lines.first()
    organization = get_organization()
    result = get_product_data(order_line, organization)
    assert 'image' not in result['itemOffered']


def test_get_product_data_with_image(
        order_with_lines_and_stock, product_with_image):
    order = order_with_lines_and_stock
    order_line = order.lines.first()
    variant = product_with_image.variants.first()
    order_line.variant = variant
    order_line.product_name = variant.display_product()
    order_line.save()
    organization = get_organization()
    result = get_product_data(order_line, organization)
    assert 'image' in result['itemOffered']
    assert result['itemOffered']['name'] == variant.display_product()


def test_get_order_confirmation_markup(order_with_lines_and_stock):
    order = order_with_lines_and_stock
    try:
        result = get_order_confirmation_markup(order)
    except TypeError:
        pytest.fail('Function output is not JSON serializable')

    try:
        # Response should be returned as a valid json
        json.loads(result)
    except ValueError:
        pytest.fail('Response is not a valid json')
