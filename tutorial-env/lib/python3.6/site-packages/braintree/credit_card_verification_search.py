from braintree.credit_card import CreditCard
from braintree.credit_card_verification import CreditCardVerification
from braintree.search import Search
from braintree.util import Constants

class CreditCardVerificationSearch:
    credit_card_cardholder_name  = Search.TextNodeBuilder("credit_card_cardholder_name")
    id                           = Search.TextNodeBuilder("id")
    credit_card_expiration_date  = Search.EqualityNodeBuilder("credit_card_expiration_date")
    credit_card_number           = Search.PartialMatchNodeBuilder("credit_card_number")
    credit_card_card_type        = Search.MultipleValueNodeBuilder("credit_card_card_type", Constants.get_all_constant_values_from_class(CreditCard.CardType))
    ids                          = Search.MultipleValueNodeBuilder("ids")
    created_at                   = Search.RangeNodeBuilder("created_at")
    status                       = Search.MultipleValueNodeBuilder("status", Constants.get_all_constant_values_from_class(CreditCardVerification.Status))
    billing_postal_code          = Search.TextNodeBuilder("billing_address_details_postal_code")
    customer_email               = Search.TextNodeBuilder("customer_email")
    customer_id                  = Search.TextNodeBuilder("customer_id")
