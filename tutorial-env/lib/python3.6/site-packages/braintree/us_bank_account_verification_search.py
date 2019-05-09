from braintree.us_bank_account import UsBankAccount
from braintree.us_bank_account_verification import UsBankAccountVerification
from braintree.search import Search
from braintree.util import Constants

class UsBankAccountVerificationSearch:
    # Text fields
    account_holder_name = Search.TextNodeBuilder("account_holder_name")
    customer_email = Search.TextNodeBuilder("customer_email")
    customer_id = Search.TextNodeBuilder("customer_id")
    id = Search.TextNodeBuilder("id")
    payment_method_token = Search.TextNodeBuilder("payment_method_token")
    routing_number = Search.TextNodeBuilder("routing_number")

    # Multiple value fields
    ids = Search.MultipleValueNodeBuilder("ids")
    status = Search.MultipleValueNodeBuilder(
        "status",
        Constants.get_all_constant_values_from_class(UsBankAccountVerification.Status)
    )
    verification_method = Search.MultipleValueNodeBuilder(
        "verification_method",
        Constants.get_all_constant_values_from_class(UsBankAccountVerification.VerificationMethod)
    )

    # Range fields
    created_at = Search.RangeNodeBuilder("created_at")

    # Equality fields
    account_type = Search.EqualityNodeBuilder("account_type")

    # Ends-with fieds
    account_number = Search.EndsWithNodeBuilder("account_number")
