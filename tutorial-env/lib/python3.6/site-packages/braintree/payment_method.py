import braintree
from braintree.address import Address
from braintree.resource import Resource
from braintree.configuration import Configuration

class PaymentMethod(Resource):
    @staticmethod
    def create(params={}):
        return Configuration.gateway().payment_method.create(params)

    @staticmethod
    def find(payment_method_token):
        return Configuration.gateway().payment_method.find(payment_method_token)

    @staticmethod
    def update(payment_method_token, params):
        return Configuration.gateway().payment_method.update(payment_method_token, params)

    @staticmethod
    def delete(payment_method_token, options={}):
        return Configuration.gateway().payment_method.delete(payment_method_token, options)

    @staticmethod
    def create_signature():
        return PaymentMethod.signature("create")

    @staticmethod
    def signature(type):
        options = [
            "fail_on_duplicate_payment_method",
            "make_default",
            "us_bank_account_verification_method",
            "verification_merchant_account_id",
            "verify_card",
            "verification_amount",
            {
                "adyen": [
                    "overwrite_brand",
                    "selected_brand"
                ]
            },
            {
                "paypal": [
                    "payee_email",
                    "order_id",
                    "custom_field",
                    "description",
                    "amount",
                    { "shipping": Address.create_signature() }
                ],
            },
        ]

        signature = [
            "billing_address_id",
            "cardholder_name",
            "customer_id",
            "cvv",
            "device_data",
            "device_session_id",
            "expiration_date",
            "expiration_month",
            "expiration_year",
            "number",
            "payment_method_nonce",
            "paypal_refresh_token",
            "paypal_vault_without_upgrade",
            "token",
            {
                "billing_address": Address.create_signature()
            },
            {
                "options": options
            }
        ]
        return signature

    @staticmethod
    def update_signature():
        signature = [
            "billing_address_id",
            "cardholder_name",
            "cvv",
            "device_session_id",
            "expiration_date",
            "expiration_month",
            "expiration_year",
            "number",
            "token",
            "venmo_sdk_payment_method_code",
            "device_data",
            "fraud_merchant_id",
            "payment_method_nonce",
            {
                "options": [
                    "make_default",
                    "us_bank_account_verification_method",
                    "verify_card",
                    "verification_amount",
                    "verification_merchant_account_id",
                    "venmo_sdk_session",
                    {
                        "adyen": [
                            "overwrite_brand",
                            "selected_brand"
                        ]
                    }
                ]
            },
            {
                "billing_address": Address.update_signature() + [{"options": ["update_existing"]}]
            }
        ]
        return signature

    @staticmethod
    def delete_signature():
        return ["revoke_all_grants"]
