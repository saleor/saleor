import logging
from decimal import Decimal

import graphene
import requests
from tqdm import tqdm

from saleor.account.models import Address, User
from saleor.channel.models import Channel
from saleor.discount.models import Voucher
from saleor.order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from saleor.payment.models import Payment, Transaction

logger = logging.getLogger(__name__)


class BaseMigration:
    @staticmethod
    def get_session(jwt_token):
        session = requests.Session()
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"JWT {jwt_token}",
            }
        )
        return session

    def clear(self):
        raise NotImplementedError()

    def migrate(self, url, token):
        raise NotImplementedError()

    @staticmethod
    def get_channel(channel_slug="default-channel"):
        channel, _ = Channel.objects.get_or_create(slug=channel_slug)
        return channel

    @staticmethod
    def get_or_create_user_address(user, address_data):
        if not address_data:
            return Address()

        address_data = {
            "phone": address_data.get("phone", ""),
            "city_area": address_data.get("cityArea", ""),
            "last_name": address_data.get("lastName", ""),
            "first_name": address_data.get("firstName", ""),
            "city": address_data.get("city").get("name", ""),
            "postal_code": address_data.get("postalCode", ""),
            "country_area": address_data.get("countryArea", ""),
            "company_name": address_data.get("companyName", ""),
            "country": address_data.get("country").get("code", ""),
            "street_address_1": address_data.get("streetAddress1", ""),
            "street_address_2": address_data.get("streetAddress2", ""),
        }
        try:
            address, _ = Address.objects.get_or_create(**address_data)
            user.addresses.add(address)
            return address
        except Address.MultipleObjectsReturned:
            addresses = Address.objects.filter(**address_data)
            user.addresses.set(addresses)

    def get_or_create_user_order(self, user, order_data):
        billing_address_id = self.get_or_create_user_address(
            user=user,
            address_data=order_data.get("billingAddress"),
        ).id
        shipping_address_id = self.get_or_create_user_address(
            user=user,
            address_data=order_data.get("shippingAddress"),
        ).id

        shipping_method = order_data.get("shippingMethod") or {}

        order_data = {
            "user": user,
            "token": order_data["token"],
            "created": order_data["created"],
            "user_email": order_data["userEmail"],
            "weight": order_data["weight"]["value"],
            "billing_address_id": billing_address_id,
            "shipping_address_id": shipping_address_id,
            "currency": order_data["total"]["currency"],
            "customer_note": order_data["customerNote"],
            "shipping_method_name": shipping_method.get("name"),
            "tracking_client_id": order_data["trackingClientId"],
            "total_net_amount": order_data["total"]["net"]["amount"],
            "display_gross_prices": order_data["displayGrossPrices"],
            "status": order_data["status"].replace("_", " ").lower(),
            "total_paid_amount": order_data["totalCaptured"]["amount"],
            "total_gross_amount": order_data["total"]["gross"]["amount"],
            "channel_id": self.get_channel(channel_slug="channel-sar").id,
            "id": int(graphene.Node.from_global_id(global_id=order_data.get("id"))[1]),
            "shipping_price_gross_amount": order_data["shippingPrice"]["gross"][
                "amount"
            ],
            "shipping_price_net_amount": order_data["shippingPrice"]["net"]["amount"],
            "voucher_id": self.get_or_create_voucher(
                voucher_data=order_data["voucher"]
            ).id,
        }
        order_obj, _ = Order.objects.get_or_create(**order_data)
        return order_obj

    @staticmethod
    def get_or_create_order_lines(order, lines_data):
        for line in lines_data:
            quantity = line.get("quantity")
            currency = line.get("unitPrice")["currency"]
            unit_price_net = line.get("unitPrice")["gross"]["amount"]
            unit_price_gross = line.get("unitPrice")["gross"]["amount"]
            line_data = {
                "order": order,
                "currency": currency,
                "quantity": quantity,
                "is_gift_card": False,
                "tax_rate": line.get("taxRate"),
                "product_sku": line.get("productSku"),
                "variant_name": line.get("variantName"),
                "product_name": line.get("productName"),
                "unit_price_gross_amount": unit_price_gross,
                "quantity_fulfilled": line.get("quantityFulfilled"),
                "is_shipping_required": line.get("isShippingRequired"),
                "translated_variant_name": line.get("translatedVariantName"),
                "translated_product_name": line.get("translatedProductName"),
                "total_price_net_amount": Decimal(unit_price_net * quantity),
                "unit_price_net_amount": line.get("unitPrice")["net"]["amount"],
                "total_price_gross_amount": Decimal(unit_price_gross * quantity),
            }
            order_line, _ = OrderLine.objects.get_or_create(**line_data)
            return order_line

    @staticmethod
    def get_or_create_order_fulfillments(line, order, fulfillments_data):
        for fulfillment in fulfillments_data:
            fulfillment_data = {
                "order": order,
                "created": fulfillment.get("created"),
                "status": fulfillment.get("status").lower(),
                "tracking_number": fulfillment.get("trackingNumber"),
                "fulfillment_order": fulfillment.get("fulfillmentOrder"),
            }
            order_fulfillment, _ = Fulfillment.objects.get_or_create(**fulfillment_data)
            order_fulfillment_line, _ = FulfillmentLine.objects.get_or_create(
                order_line=line, fulfillment=order_fulfillment, quantity=line.quantity
            )
            return order_fulfillment

    @staticmethod
    def get_or_create_order_payment_transactions(payment, transactions_data):
        for transaction in transactions_data:
            amount = transaction.get("amount", {})
            transaction_data = {
                "payment": payment,
                "already_processed": True,
                "amount": amount.get("amount"),
                "currency": amount.get("currency"),
                "created": transaction.get("created"),
                "kind": transaction.get("kind").lower(),
                "is_success": transaction.get("isSuccess"),
                "gateway_response": transaction.get("gatewayResponse"),
            }
            order_payment_transaction, _ = Transaction.objects.get_or_create(
                **transaction_data
            )
            return order_payment_transaction

    def get_or_create_order_payments(self, order, payments_data):
        for payment in payments_data:
            billing_address = payment.get("billingAddress", {})
            payment_data = {
                "order": order,
                "token": payment.get("token"),
                "gateway": payment.get("gateway"),
                "created": payment.get("created"),
                "is_active": payment.get("isActive"),
                "psp_reference": payment.get("token"),
                "extra_data": payment.get("extraData"),
                "total": payment.get("total")["amount"],
                "currency": payment.get("total")["currency"],
                "billing_email": payment.get("billingEmail"),
                "billing_last_name": billing_address.get("lastName"),
                "billing_city_area": billing_address.get("cityArea"),
                "billing_first_name": billing_address.get("firstName"),
                "customer_ip_address": payment.get("customerIpAddress"),
                "billing_postal_code": billing_address.get("postalCode"),
                "billing_company_name": billing_address.get("companyName"),
                "billing_address_1": billing_address.get("streetAddress1"),
                "billing_address_2": billing_address.get("streetAddress2"),
                "captured_amount": payment.get("capturedAmount")["amount"],
                "billing_city": billing_address.get("city", {}).get("name"),
                "billing_country_area": billing_address.get("countryArea", {}),
                "billing_country_code": billing_address.get("country", {}).get("code"),
                "charge_status": payment.get("chargeStatus").replace("_", "-").lower(),
            }
            order_payment, _ = Payment.objects.get_or_create(**payment_data)
            self.get_or_create_order_payment_transactions(
                order_payment, payment.get("transactions")
            )
            return order_payment

    @staticmethod
    def get_or_create_voucher(voucher_data):
        if not voucher_data:
            return Voucher()

        voucher_data = {
            "code": voucher_data.get("code"),
            "used": voucher_data.get("used"),
            "end_date": voucher_data.get("endDate"),
            "type": voucher_data.get("type").lower(),
            "start_date": voucher_data.get("startDate"),
            "usage_limit": voucher_data.get("usageLimit"),
            "apply_once_per_order": voucher_data.get("applyOncePerOrder"),
            "apply_once_per_customer": voucher_data.get("applyOncePerCustomer"),
            "discount_value_type": voucher_data.get("discountValueType").lower(),
            "min_checkout_items_quantity": voucher_data.get("minCheckoutItemsQuantity"),
            "id": int(
                graphene.Node.from_global_id(global_id=voucher_data.get("id"))[1]
            ),
        }
        voucher_obj, _ = Voucher.objects.get_or_create(
            code=voucher_data.get("code"), defaults=voucher_data
        )
        return voucher_obj


USER_QUERY = """
query CUSTOMER {
  user(id: "user_id") {
    role
    phone
    gender
    birthday
    isFeatured
    permissionGender
    orders(first: 100) {
      edges {
        node {
          id
          status
          totalCaptured {
            currency
            amount
          }
          payments {
            transactions {
              created
              token
              kind
              isSuccess
              error
              amount {
                currency
                amount
              }
              gatewayResponse
            }
            isActive
            gateway
            created
            modified
            chargeStatus
            billingAddress {
              firstName
              lastName
              companyName
              streetAddress1
              streetAddress2
              city {
                name
              }
              cityArea
              postalCode
              country {
                code
              }
              countryArea
            }
            billingEmail
            customerIpAddress
            extraData
            token
            total {
              amount
              currency
            }
            capturedAmount {
              currency
              amount
            }
          }
          displayGrossPrices
          fulfillments {
            fulfillmentOrder
            status
            trackingNumber
            created
            statusDisplay
          }
          lines {
            productName
            translatedVariantName
            translatedProductName
            variantName
            productSku
            quantity
            unitPrice {
              currency
              net {
                amount
              }
              gross {
                amount
              }
            }
            isShippingRequired
            taxRate
            quantityFulfilled
            variantName
          }
          voucher {
            id
            name
            type
            code
            usageLimit
            used
            startDate
            endDate
            applyOncePerOrder
            applyOncePerCustomer
            discountValueType
            discountValue
          }
          total {
            gross {
              amount
            }
          }
          shippingPrice {
            gross {
              amount
            }
            net {
              amount
            }
          }
          total {
            currency
            net {
              amount
            }
          }
          userEmail
          shippingMethod {
            name
          }
          token
          customerNote
          weight {
            value
          }
          billingAddress {
            id
            firstName
            lastName
            companyName
            streetAddress1
            streetAddress2
            city {
              name
            }
            postalCode
            country {
              code
            }
            countryArea
            phone
            cityArea
          }
          shippingAddress {
            id
            firstName
            lastName
            companyName
            streetAddress1
            streetAddress2
            city {
              name
            }
            postalCode
            country {
              code
            }
            countryArea
            phone
            cityArea
          }
          languageCode
          created
          trackingClientId
        }
      }
    }
    addresses {
      id
      firstName
      lastName
      companyName
      streetAddress1
      streetAddress2
      city {
        name
      }
      postalCode
      country {
        code
      }
      countryArea
      phone
      cityArea
    }
  }
}
"""


class DataMigration(BaseMigration):
    def clear(self):
        User.objects.all().exclude(email="admin@example.com").delete()
        Transaction.objects.all().delete()
        Payment.objects.all().delete()
        Order.objects.all().delete()

    def migrate(self, url, token):

        # Get all users from old database
        users = User.objects.using("datamigration").raw(
            """SELECT id, first_name, last_name, avatar, is_staff, password,
            is_active, last_login, date_joined from account_user
            order by date_joined desc"""
        )
        for user in tqdm(
            ascii=True,
            total=len(users),
            desc="Data migration",
            iterable=users.iterator(),
        ):
            created_user, created = User.objects.get_or_create(
                email=user.email,
                defaults={
                    "avatar": user.avatar,
                    "is_staff": user.is_staff,
                    "password": user.password,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "first_name": user.first_name,
                    "last_login": user.last_login,
                    "date_joined": user.date_joined,
                },
            )
            if created:
                user_global_id = graphene.Node.to_global_id("User", user.id)
                user_query = USER_QUERY.replace("user_id", user_global_id)
                response = (
                    self.get_session(jwt_token=token)
                    .post(url=url, json={"query": user_query})
                    .json()
                )
                user_data = response.get("data", {}).get("user")
                if not response.get("errors") and user_data:
                    gender = user_data.get("gender", "")
                    birthday = user_data.get("birthday", "")
                    user_data.update(
                        {
                            "role": user_data.get("role", ""),
                            "gender": gender if gender else "",
                            "phone": user_data.get("phone", ""),
                            "birthday": birthday if birthday else "",
                            "isFeatured": user_data.get("isFeatured", False),
                            "permissionGender": user_data.get("permissionGender", ""),
                        }
                    )
                    created_user.store_value_in_private_metadata(items=user_data)
                    created_user.save(update_fields=["private_metadata"])

                    # Migrate addresses
                    user_addresses = user_data.get("addresses", [])
                    if user_addresses:
                        for address_data in user_addresses:
                            self.get_or_create_user_address(created_user, address_data)

                    # Migrate user's orders
                    edges = user_data.get("orders", [{}]).get("edges", [])
                    if edges:
                        for edge in edges:
                            order_data = edge.get("node")
                            created_order = self.get_or_create_user_order(
                                user=created_user, order_data=order_data
                            )
                            lines = order_data.get("lines", [])
                            line = self.get_or_create_order_lines(
                                order=created_order, lines_data=lines
                            )
                            fulfillments = order_data.get("fulfillments", [])
                            self.get_or_create_order_fulfillments(
                                line=line,
                                order=created_order,
                                fulfillments_data=fulfillments,
                            )
                            payments = order_data.get("payments", [])
                            self.get_or_create_order_payments(
                                order=created_order, payments_data=payments
                            )
