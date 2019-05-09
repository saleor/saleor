from braintree.credit_card import CreditCard
from braintree.search import Search
from braintree.transaction import Transaction
from braintree.util import Constants

class TransactionSearch:
    billing_first_name           = Search.TextNodeBuilder("billing_first_name")
    billing_company              = Search.TextNodeBuilder("billing_company")
    billing_country_name         = Search.TextNodeBuilder("billing_country_name")
    billing_extended_address     = Search.TextNodeBuilder("billing_extended_address")
    billing_first_name           = Search.TextNodeBuilder("billing_first_name")
    billing_last_name            = Search.TextNodeBuilder("billing_last_name")
    billing_locality             = Search.TextNodeBuilder("billing_locality")
    billing_postal_code          = Search.TextNodeBuilder("billing_postal_code")
    billing_region               = Search.TextNodeBuilder("billing_region")
    billing_street_address       = Search.TextNodeBuilder("billing_street_address")
    credit_card_cardholder_name  = Search.TextNodeBuilder("credit_card_cardholder_name")
    currency                     = Search.TextNodeBuilder("currency")
    customer_company             = Search.TextNodeBuilder("customer_company")
    customer_email               = Search.TextNodeBuilder("customer_email")
    customer_fax                 = Search.TextNodeBuilder("customer_fax")
    customer_first_name          = Search.TextNodeBuilder("customer_first_name")
    customer_id                  = Search.TextNodeBuilder("customer_id")
    customer_last_name           = Search.TextNodeBuilder("customer_last_name")
    customer_phone               = Search.TextNodeBuilder("customer_phone")
    customer_website             = Search.TextNodeBuilder("customer_website")
    id                           = Search.TextNodeBuilder("id")
    order_id                     = Search.TextNodeBuilder("order_id")
    payment_method_token         = Search.TextNodeBuilder("payment_method_token")
    processor_authorization_code = Search.TextNodeBuilder("processor_authorization_code")
    europe_bank_account_iban       = Search.TextNodeBuilder("europe_bank_account_iban")
    settlement_batch_id          = Search.TextNodeBuilder("settlement_batch_id")
    shipping_company             = Search.TextNodeBuilder("shipping_company")
    shipping_country_name        = Search.TextNodeBuilder("shipping_country_name")
    shipping_extended_address    = Search.TextNodeBuilder("shipping_extended_address")
    shipping_first_name          = Search.TextNodeBuilder("shipping_first_name")
    shipping_last_name           = Search.TextNodeBuilder("shipping_last_name")
    shipping_locality            = Search.TextNodeBuilder("shipping_locality")
    shipping_postal_code         = Search.TextNodeBuilder("shipping_postal_code")
    shipping_region              = Search.TextNodeBuilder("shipping_region")
    shipping_street_address      = Search.TextNodeBuilder("shipping_street_address")
    paypal_payer_email           = Search.TextNodeBuilder("paypal_payer_email")
    paypal_payment_id            = Search.TextNodeBuilder("paypal_payment_id")
    paypal_authorization_id      = Search.TextNodeBuilder("paypal_authorization_id")
    credit_card_unique_identifier = Search.TextNodeBuilder("credit_card_unique_identifier")

    credit_card_expiration_date  = Search.EqualityNodeBuilder("credit_card_expiration_date")
    credit_card_number           = Search.PartialMatchNodeBuilder("credit_card_number")
    
    user                         = Search.MultipleValueNodeBuilder("user")
    ids                          = Search.MultipleValueNodeBuilder("ids")
    merchant_account_id          = Search.MultipleValueNodeBuilder("merchant_account_id")
    payment_instrument_type      = Search.MultipleValueNodeBuilder("payment_instrument_type")

    created_using = Search.MultipleValueNodeBuilder(
        "created_using",
        Constants.get_all_constant_values_from_class(Transaction.CreatedUsing)
    )

    credit_card_card_type = Search.MultipleValueNodeBuilder(
        "credit_card_card_type",
        Constants.get_all_constant_values_from_class(CreditCard.CardType)
    )

    credit_card_customer_location = Search.MultipleValueNodeBuilder(
        "credit_card_customer_location",
        Constants.get_all_constant_values_from_class(CreditCard.CustomerLocation)
    )

    source = Search.MultipleValueNodeBuilder("source")

    status = Search.MultipleValueNodeBuilder(
        "status",
        Constants.get_all_constant_values_from_class(Transaction.Status)
    )

    type = Search.MultipleValueNodeBuilder(
        "type",
        Constants.get_all_constant_values_from_class(Transaction.Type)
    )

    refund = Search.KeyValueNodeBuilder("refund")

    amount = Search.RangeNodeBuilder("amount")
    authorization_expired_at = Search.RangeNodeBuilder("authorization_expired_at")
    authorized_at = Search.RangeNodeBuilder("authorized_at")
    created_at = Search.RangeNodeBuilder("created_at")
    disbursement_date = Search.RangeNodeBuilder("disbursement_date")
    dispute_date = Search.RangeNodeBuilder("dispute_date")
    failed_at = Search.RangeNodeBuilder("failed_at")
    gateway_rejected_at = Search.RangeNodeBuilder("gateway_rejected_at")
    processor_declined_at = Search.RangeNodeBuilder("processor_declined_at")
    settled_at = Search.RangeNodeBuilder("settled_at")
    submitted_for_settlement_at = Search.RangeNodeBuilder("submitted_for_settlement_at")
    voided_at = Search.RangeNodeBuilder("voided_at")
