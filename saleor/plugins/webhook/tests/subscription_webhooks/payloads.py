import json

import graphene
from django.utils import timezone

from ..... import __version__
from .....core.utils import build_absolute_uri
from .....graphql.attribute.enums import AttributeInputTypeEnum, AttributeTypeEnum
from .....graphql.shop.types import SHOP_ID
from .....product.models import Product


def generate_account_events_payload(customer_user):
    payload = {
        **generate_customer_payload(customer_user),
    }

    return json.dumps(payload)


def generate_account_requested_events_payload(customer_user, channel, new_email=None):
    payload = {
        **generate_customer_payload(customer_user),
        **{
            "token": "token",
            "redirectUrl": "http://www.mirumee.com?token=token",
            "channel": {
                "slug": channel.slug,
                "id": graphene.Node.to_global_id("Channel", channel.id),
            }
            if channel
            else None,
            "shop": {"domain": {"host": "mirumee.com", "url": "http://mirumee.com/"}},
        },
    }
    if new_email:
        payload["newEmail"] = new_email

    return json.dumps(payload)


def generate_app_payload(app, app_global_id):
    return json.dumps(
        {
            "app": {
                "id": app_global_id,
                "isActive": app.is_active,
                "name": app.name,
                "appUrl": app.app_url,
            }
        }
    )


def generate_attribute_payload(attribute):
    return json.dumps(
        {
            "attribute": {
                "name": attribute.name,
                "slug": attribute.slug,
                "type": AttributeTypeEnum.get(attribute.type).name,
                "inputType": AttributeInputTypeEnum.get(attribute.input_type).name,
            }
        }
    )


def generate_attribute_value_payload(attribute_value):
    return json.dumps(
        {
            "attributeValue": {
                "name": attribute_value.name,
                "slug": attribute_value.slug,
                "value": attribute_value.value,
            }
        }
    )


def generate_taxed_money_payload(taxed_money):
    return {
        "currency": taxed_money.currency,
        "gross": {"amount": float(taxed_money.gross.amount)},
        "net": {"amount": float(taxed_money.net.amount)},
    }


def generate_variant_payload(variant):
    return {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "name": variant.name,
        "product": {
            "id": graphene.Node.to_global_id("Product", variant.product.pk),
            "name": variant.product.name,
        },
    }


def generate_fulfillment_lines_payload(fulfillment):
    lines = fulfillment.lines.all()
    lines = sorted(lines, key=lambda d: d.pk)
    return [
        {
            "id": graphene.Node.to_global_id("FulfillmentLine", line.pk),
            "quantity": line.quantity,
            "orderLine": {
                "variant": generate_variant_payload(line.order_line.variant),
                "unitPrice": generate_taxed_money_payload(line.order_line.unit_price),
            },
        }
        for line in lines
    ]


def generate_fulfillment_payload(fulfillment, add_notify_customer_field=False):
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)
    payload = {
        "fulfillment": {
            "id": fulfillment_id,
            "fulfillmentOrder": fulfillment.fulfillment_order,
            "trackingNumber": fulfillment.tracking_number,
            "status": fulfillment.status.upper(),
            "lines": generate_fulfillment_lines_payload(fulfillment),
        },
        "order": {
            "id": graphene.Node.to_global_id("Order", fulfillment.order.pk),
        },
    }
    if add_notify_customer_field:
        payload["notifyCustomer"] = True
    return payload


def generate_address_payload(address):
    return {
        "firstName": address.first_name,
        "lastName": address.last_name,
        "companyName": address.company_name,
        "streetAddress1": address.street_address_1,
        "streetAddress2": address.street_address_2,
        "city": address.city,
        "cityArea": address.city_area,
        "postalCode": address.postal_code,
        "countryArea": address.country_area,
        "phone": str(address.phone),
        "country": {"code": address.country.code},
    }


def generate_customer_payload(customer):
    addresses = sorted(customer.addresses.all(), key=lambda address: address.pk)
    return {
        "user": {
            "email": customer.email,
            "firstName": customer.first_name,
            "lastName": customer.last_name,
            "isStaff": customer.is_staff,
            "isActive": customer.is_active,
            "addresses": [
                {"id": graphene.Node.to_global_id("Address", address.pk)}
                for address in addresses
            ],
            "languageCode": customer.language_code.upper(),
            "defaultShippingAddress": (
                generate_address_payload(customer.default_shipping_address)
                if customer.default_shipping_address
                else None
            ),
            "defaultBillingAddress": (
                generate_address_payload(customer.default_billing_address)
                if customer.default_billing_address
                else None
            ),
        }
    }


def generate_staff_payload(staff_user):
    return {
        "user": {
            "email": staff_user.email,
            "firstName": staff_user.first_name,
            "lastName": staff_user.last_name,
            "isStaff": True,
            "isActive": staff_user.is_active,
        }
    }


def generate_collection_payload(collection):
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    products = sorted(collection.products.all(), key=lambda product: product.name)
    products_node = [
        {
            "node": {
                "id": graphene.Node.to_global_id("Product", product.pk),
                "name": product.name,
            }
        }
        for product in products
    ]
    return {
        "collection": {
            "id": collection_id,
            "name": collection.name,
            "slug": collection.slug,
            "channel": "main",
            "products": {"edges": products_node},
        }
    }


def generate_page_payload(page):
    page_id = graphene.Node.to_global_id("Page", page.pk)
    page_type_id = graphene.Node.to_global_id("PageType", page.page_type.pk)
    page_attributes = page.page_type.page_attributes.all()
    attribute_values_1 = page_attributes[0].values.first()
    return {
        "page": {
            "id": page_id,
            "title": page.title,
            "content": json.dumps(page.content),
            "slug": page.slug,
            "isPublished": page.is_published,
            "publishedAt": page.published_at,
            "pageType": {"id": page_type_id},
            "attributes": [
                {
                    "attribute": {"slug": page_attributes[0].slug},
                    "values": [
                        {
                            "slug": attribute_values_1.slug,
                            "name": attribute_values_1.name,
                            "reference": None,
                            "date": None,
                            "dateTime": None,
                            "file": None,
                        }
                    ],
                },
                {"attribute": {"slug": page_attributes[1].slug}, "values": []},
            ],
        }
    }


def generate_page_type_payload(page_type):
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    return {
        "pageType": {
            "id": page_type_id,
            "name": page_type.name,
            "slug": page_type.slug,
            "attributes": [
                {"slug": ap.attribute.slug} for ap in page_type.attributepage.all()
            ],
        }
    }


def generate_permission_group_payload(group):
    return {
        "permissionGroup": {
            "name": group.name,
            "permissions": [
                {"name": permission.name} for permission in group.permissions.all()
            ],
            "users": [{"email": user.email} for user in group.user_set.all()],
        }
    }


def generate_invoice_payload(invoice):
    payload = {
        "invoice": {
            "id": graphene.Node.to_global_id("Invoice", invoice.pk),
            "status": invoice.status.upper(),
            "number": invoice.number,
            "order": None,
        }
    }
    if invoice.order_id:
        order_id = graphene.Node.to_global_id("Order", invoice.order_id)
        payload["invoice"]["order"] = {"id": order_id}
        payload["order"] = {
            "id": order_id,
            "number": str(invoice.order.number),
            "userEmail": invoice.order.user_email,
            "isPaid": invoice.order.is_fully_paid(),
        }
    return payload


def generate_category_payload(category):
    tree = category.get_descendants(include_self=True)
    products = sorted(
        Product.objects.all().filter(category__in=tree),
        key=lambda product: product.name,
    )
    return {
        "category": {
            "id": graphene.Node.to_global_id("Category", category.id),
            "name": category.name,
            "ancestors": {"edges": []},
            "children": {"edges": [{"node": {"name": category.children.first().name}}]},
            "products": {
                "edges": [
                    {
                        "node": {
                            "id": graphene.Node.to_global_id("Product", product.id),
                            "name": product.name,
                        }
                    }
                    for product in products
                ]
            },
        }
    }


def generate_shipping_method_payload(shipping_method):
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.id
    )
    shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_method.shipping_zone.id
    )
    channel_listings = sorted(
        shipping_method.channel_listings.all(), key=lambda cl: cl.pk
    )
    return {
        "shippingMethod": {
            "id": shipping_method_id,
            "name": shipping_method.name,
            "channelListings": [
                {"channel": {"name": sl.channel.name}} for sl in channel_listings
            ],
        },
        "shippingZone": {
            "id": shipping_zone_id,
            "name": shipping_method.shipping_zone.name,
        },
    }


def generate_sale_payload(sale):
    return {
        "sale": {
            "id": graphene.Node.to_global_id("Sale", sale.pk),
            "name": sale.name,
            "startDate": sale.start_date.isoformat(),
            "endDate": None,
            "categories": {
                "edges": [
                    {
                        "node": {
                            "id": graphene.Node.to_global_id("Category", category.pk),
                            "name": category.name,
                        }
                    }
                    for category in sale.categories.all()
                ]
            },
        }
    }


def generate_voucher_payload(voucher, voucher_global_id):
    return json.dumps(
        {
            "voucher": {
                "id": voucher_global_id,
                "name": voucher.name,
                "code": voucher.code,
                "usageLimit": voucher.usage_limit,
            }
        }
    )


def generate_voucher_created_payload_with_meta(
    voucher, voucher_global_id, requestor, requestor_type, webhook_app
):
    data = {
        "__typename": "VoucherCreated",
        "issuedAt": timezone.now().isoformat(),
        "version": __version__,
        "issuingPrincipal": None,
        "recipient": {
            "id": graphene.Node.to_global_id("App", webhook_app.id),
            "name": webhook_app.name,
        },
        "voucher": {
            "id": voucher_global_id,
            "name": voucher.name,
            "code": voucher.code,
            "usageLimit": voucher.usage_limit,
        },
    }

    if requestor_type == "user":
        data["issuingPrincipal"] = {
            "__typename": "User",
            "id": graphene.Node.to_global_id("User", requestor.id),
            "email": requestor.email,
        }

    if requestor_type == "app":
        data["issuingPrincipal"] = {
            "__typename": "App",
            "id": graphene.Node.to_global_id("App", requestor.id),
            "name": requestor.name,
        }

    return json.dumps(data)


def generate_gift_card_payload(gift_card, card_global_id):
    return json.dumps(
        {
            "giftCard": {
                "id": card_global_id,
                "isActive": gift_card.is_active,
                "code": gift_card.code,
                "createdBy": {"email": gift_card.created_by.email},
            }
        }
    )


def generate_export_payload(export_file, export_global_id):
    return json.dumps(
        {
            "export": {
                "id": export_global_id,
                "createdAt": export_file.created_at.isoformat(),
                "updatedAt": export_file.updated_at.isoformat(),
                "status": export_file.status.upper(),
                "url": build_absolute_uri(export_file.content_file.url),
                "message": export_file.message,
            }
        }
    )


def generate_menu_payload(menu, menu_global_id):
    menu_items = sorted(menu.items.all(), key=lambda key: key.pk)
    return {
        "menu": {
            "id": menu_global_id,
            "name": menu.name,
            "slug": menu.slug,
            "items": [
                {
                    "id": graphene.Node.to_global_id(item.id, "MenuItem"),
                    "name": item.name,
                }
                for item in menu_items
            ],
        }
    }


def generate_menu_item_payload(menu_item, menu_item_global_id):
    menu = (
        {"id": graphene.Node.to_global_id("Menu", menu_item.menu_id)}
        if menu_item.menu_id
        else None
    )
    page = (
        {"id": graphene.Node.to_global_id("Page", menu_item.page_id)}
        if menu_item.page_id
        else None
    )
    return {
        "menuItem": {
            "id": menu_item_global_id,
            "name": menu_item.name,
            "menu": menu,
            "page": page,
        }
    }


def generate_warehouse_payload(warehouse, warehouse_global_id):
    return json.dumps(
        {
            "warehouse": {
                "id": warehouse_global_id,
                "name": warehouse.name,
                "shippingZones": {
                    "edges": [
                        {
                            "node": {
                                "id": graphene.Node.to_global_id(
                                    "ShippingZone", zone.id
                                )
                            }
                        }
                        for zone in warehouse.shipping_zones.all()
                    ]
                },
                "address": {"companyName": warehouse.address.company_name},
            }
        }
    )


def generate_payment_payload(payment):
    total = payment.get_total()
    return {
        "payment": {
            "id": graphene.Node.to_global_id("Payment", payment.pk),
            "total": {"amount": float(total.amount), "currency": total.currency},
            "gateway": payment.gateway,
            "isActive": payment.is_active,
        }
    }


def generate_shop_payload():
    return json.dumps(
        {
            "shop": {
                "id": graphene.Node.to_global_id("Shop", SHOP_ID),
            }
        }
    )
