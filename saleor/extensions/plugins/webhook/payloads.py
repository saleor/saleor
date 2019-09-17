from typing import TYPE_CHECKING

from .serializer import WebhookSerializer

if TYPE_CHECKING:
    from ....order.models import Order
    from ....account.models import User


def generate_order_payload(order: "Order"):
    serializer = WebhookSerializer()
    lines_data = serializer.serialize(
        order.lines.all(),
        fields=(
            "product_name",
            "variant_name",
            "translated_product_name",
            "translated_variant_name",
            "product_sku",
            "quantity",
            "currency",
            "unit_price_net_amount",
            "unit_price_gross_amount",
            "tax_rate",
        ),
    )
    order_data = serializer.serialize(
        [order],
        fields=(
            "created"
            "status"
            "user_email"
            "currency"
            "shipping_method_name"
            "shipping_price_net_amount"
            "shipping_price_gross_amount"
            "token"
            "total_net_amount"
            "total_gross_amount"
            "discount_amount"
            "discount_name"
        ),
        additional_fields={
            "lines": lines_data,
            "shipping_address": order.shipping_address.as_data(),
            "billing_address": order.billing_address.as_data(),
        },
    )
    return order_data


def generate_customer_payload(customer: "User"):
    serializer = WebhookSerializer()
    data = serializer.serialize(
        [customer],
        fields=[
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "default_shipping_address",
            "default_billing_address",
        ],
        additional_fields={
            "default_shipping_address": customer.default_billing_address.as_data(),
            "default_billing_address": customer.default_shipping_address.as_data(),
        },
    )
    return data
