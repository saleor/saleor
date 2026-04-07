from unittest.mock import sentinel

import pytest

from ....core.taxes import TaxType


@pytest.fixture
def tax_type():
    return TaxType(
        code="code_2",
        description="description_2",
    )


def test_get_tax_code_from_object_meta_no_app(
    webhook_plugin,
    product,
):
    # given
    plugin = webhook_plugin()
    previous_value = sentinel.PREVIOUS_VALUE

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, previous_value)

    # then
    assert fetched_tax_type == previous_value


def test_get_tax_code_from_object_meta(
    webhook_plugin,
    tax_app,
    tax_type,
    product,
):
    # given
    plugin = webhook_plugin()
    product.metadata = {
        f"{tax_app.identifier}.code": tax_type.code,
        f"{tax_app.identifier}.description": tax_type.description,
    }

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, None)

    # then
    assert fetched_tax_type == tax_type


def test_get_tax_code_from_object_meta_default_code(
    webhook_plugin,
    tax_app,
    product,
):
    # given
    plugin = webhook_plugin()

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, None)

    # then
    assert fetched_tax_type == TaxType(
        code="UNMAPPED",
        description="Unmapped Product/Product Type",
    )
