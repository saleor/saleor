import requests
from django.contrib.sites.models import Site

from saleor.celeryconf import app


def get_oto_auth_credentials(config):
    retailer_id = config.get("RETAILER_ID")
    retailer_token = config.get("RETAILER_TOKEN")
    return dict(retailerId=retailer_id, password=retailer_token)


def get_order_customer_data(order):
    return {
        "name": order.user.get_full_name(),
        "email": order.get_customer_email(),
        "city": order.shipping_address.city,
        "district": order.shipping_address.city_area,
        "mobile": order.shipping_address.phone.as_e164,
        "country": order.shipping_address.country.code,
        "postcode": order.shipping_address.postal_code,
        "address": order.shipping_address.street_address_1
        or order.shipping_address.street_address_2,
    }


def get_order_items_data(order):
    site = Site.objects.get_current()
    return [
        {
            "sku": line.product_sku,
            "name": line.product_name,
            "quantity": line.quantity_fulfilled,
            "productId": line.variant.product.id,
            "price": line.total_price_net_amount,
            "image": "%s%s"
            % (site.domain, line.variant.product.get_first_image().image.url)
            if line.variant.product.get_first_image()
            else "",
        }
        for line in order.lines.all()
    ]


def generate_create_order_data(fulfillment):
    fulfillment_line = fulfillment.lines.last()
    is_cod_order = (
        True
        if fulfillment.order.get_last_payment().payment_method_type == "cod"
        else False
    )
    data = {
        "storeName": "WeCre8",
        "orderId": str(fulfillment.id),
        "ref1": fulfillment.order.token,
        "currency": fulfillment.order.currency,
        "shippingNotes": fulfillment.order.customer_note,
        "payment_method": "cod" if is_cod_order else "paid",
        "items": get_order_items_data(order=fulfillment.order),
        "subtotal": fulfillment.order.get_subtotal().net.amount,
        "customer": get_order_customer_data(order=fulfillment.order),
        "shippingAmount": fulfillment.order.shipping_price_net_amount,
        "amount_due": fulfillment.order.total_net_amount if is_cod_order else 0,
        "amount": fulfillment_line.quantity
        * fulfillment_line.order_line.unit_price_net_amount,
        "orderDate": "%s %s:%s"
        % (
            str(fulfillment.order.created.date().strftime("%d/%m/%Y")),
            str(fulfillment.order.created.hour),
            str(fulfillment.order.created.minute),
        ),
    }
    return data


def generate_cancel_order_and_return_link_data(fulfillment):
    return dict(
        orderId=str(fulfillment.id),
    )


def generate_oto_request_data(fulfillment, **kwargs):
    destination_url = kwargs.get("destination_url")
    if destination_url == "createOrder":
        return generate_create_order_data(fulfillment=fulfillment)
    elif destination_url == "cancelOrder":
        return generate_cancel_order_and_return_link_data(fulfillment=fulfillment)
    elif destination_url == "getReturnLink":
        return generate_cancel_order_and_return_link_data(fulfillment=fulfillment)


def get_oto_url(destination_url):
    return "https://api.tryoto.com/rest/v2/{0}".format(destination_url)


@app.task
def send_oto_request(fulfillment, config, destination_url):
    """Send request to OTO API."""
    data = generate_oto_request_data(
        fulfillment=fulfillment, destination_url=destination_url
    )
    url = get_oto_url(destination_url=destination_url)
    response = requests.post(
        url=url,
        json=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(config.get("ACCESS_TOKEN")),
        },
    )
    return response.json()
