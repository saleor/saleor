import pytest


@pytest.fixture
def tax_line_data_response():
    return {
        "id": "1234",
        "currency": "PLN",
        "unit_net_amount": 12.34,
        "unit_gross_amount": 12.34,
        "total_gross_amount": 12.34,
        "total_net_amount": 12.34,
    }


@pytest.fixture
def tax_data_response(tax_line_data_response):
    return {
        "currency": "PLN",
        "total_net_amount": 12.34,
        "total_gross_amount": 12.34,
        "subtotal_net_amount": 12.34,
        "subtotal_gross_amount": 12.34,
        "shipping_price_gross_amount": 12.34,
        "shipping_price_net_amount": 12.34,
        "lines": [tax_line_data_response] * 5,
    }
