"""We are NOT handling errors from:
- Braintree Marketplace
- Dispute
- Apple Pay
- OAuth
- Venmo
- Search
- Recurring Billing
- 3D Secure
- Customer
as they are not currently supported.

For the full list of errors please refer to:
https://developers.braintreepayments.com/reference/general/validation-errors/all/python#transaction
"""
from ... import TransactionError

INVALID_EXPIRY_DATE_ERRORS = [
    '81709',  # Expiration date is required.
    '81710',  # Expiration date is invalid.
    '81711',  # Expiration year is invalid. It must be between 1975 and 2201.
    '81712',  # Expiration month is invalid.
    '81713',  # Expiration year is invalid.
]
INCORRECT_ZIP_ERRORS = [
    '81813',  # ZIP can only contain letters, numbers, spaces, and hyphens.
    '81808',  # ZIP is required.
    '81809',  # ZIP may contain no more than 9 letter or number characters.
    '81737',  # ZIP verification failed.
    '91826',  # ZIP must be a string.
    '94527',  # Billing postal code format is invalid.
    '915164',  # Shipping amount is too large.
    '915165',  # Ships from postal code is too long.
    '915166',  # Ships from postal code must be a string.
    '915167',  # Ships from zip can only contain letters, numbers, spaces, and hyphens.
]
INCORRECT_CVV_ERRORS = [
    '81706',  # CVV is required.
    '81707',  # CVV must be 4 digits for AmericanExpress and 3 digits for other
]
INVALID_CVV_ERRORS = [
    '81736'  # CVV verification failed.
]
INVALID_NUMBER_ERRORS = [
    '81750',  # Credit card number is prohibited.
    '81715',  # Credit card number is invalid.
]
INCORRECT_NUMBER_ERRORS = [
    '81714',  # Credit card number is required.
    '81718',  # Credit card number cannot be updated to an unsupported card
              # type when it is associated to subscriptions.
    '81716',  # Credit card number must be 12-19 digits.
    '81717',  # Credit card number is not an accepted test number.
]
INCORRECT_ADDRESS_ERRORS = [
    '81801',  # Addresses must have at least one field filled in.
    '81802',  # Company is too long.
    '81804',  # Extended address is too long.
    '81805',  # First name is too long.
    '81806',  # Last name is too long.
    '81807',  # Locality is too long.
    '81810',  # Region is too long.
    '81811',  # Street address is required.
    '81812',  # Street address is too long.
    '81827',  # US state codes must be two characters to meet PayPal Seller
              # Protection requirements.
    '91803',  # Country name is not an accepted country.
    '91815',  # Provided country information is inconsistent.
    '91816',  # Country code (alpha3) is not an accepted country.
    '91817',  # Country code (numeric) is not an accepted country.
    '91814',  # Country code (alpha2) is not an accepted country.
    '91818',  # Customer has already reached the maximum of 50 addresses.
    '91819',  # First name must be a string.
    '91820',  # Last name must be a string.
    '91821',  # Company must be a string.
    '91822',  # Street address must be a string.
    '91823',  # Extended address must be a string.
    '91824',  # Locality must be a string.
    '91825',  # Region must be a string.
    '91828',  # Address is invalid.
    '918996',  # Required attribute is missing
    '918997',  # Attribute is not in the required format
    '918998',  # Attribute is not in the list of expected values
    '918999',  # Attribute is the wrong type
]
EXPIRED_ERRORS = [
    '93108',  # Unknown or expired payment_method_nonce.
    '91732',  # Unknown or expired payment_method_nonce.
    '92908',  # Unknown or expired payment_method_nonce.
    '92911',  # PayPal authentication expired.
    '91565',  # Unknown or expired payment_method_nonce.
]

DEFAULT_ERROR_TYPE = TransactionError.PROCESSING_ERROR
ERRORS = {
    TransactionError.INCORRECT_NUMBER: INCORRECT_NUMBER_ERRORS,
    TransactionError.INVALID_NUMBER: INVALID_NUMBER_ERRORS,
    TransactionError.INCORRECT_CVV: INCORRECT_CVV_ERRORS,
    TransactionError.INVALID_CVV: INVALID_CVV_ERRORS,
    TransactionError.INCORRECT_ZIP: INCORRECT_ZIP_ERRORS,
    TransactionError.INCORRECT_ADDRESS: INCORRECT_ADDRESS_ERRORS,
    TransactionError.INVALID_EXPIRY_DATE: INVALID_EXPIRY_DATE_ERRORS,
    TransactionError.EXPIRED: EXPIRED_ERRORS,
    TransactionError.PROCESSING_ERROR: [],
    TransactionError.DECLINED: []}


def get_error_type(error_code):
    for error_type, error_codes in ERRORS:
        if error_code in error_codes:
            return error_type
    return DEFAULT_ERROR_TYPE


DEFAULT_ERROR_MESSAGE = (
    'Unable to process the transaction. '
    'Transaction\'s token is incorrect or expired.')


class BraintreeException(Exception):
    pass
