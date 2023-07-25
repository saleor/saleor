from enum import Enum


class PaymentError(Exception):
    def __init__(self, message, code=None):
        super(PaymentError, self).__init__(message, code)
        self.message = message
        self.code = code

    def __str__(self):
        return self.message


class GatewayError(IOError):
    pass


class CustomPaymentChoices:
    MANUAL = "manual"

    CHOICES = [(MANUAL, "Manual")]


class OperationType(Enum):
    PROCESS_PAYMENT = "process_payment"
    AUTH = "authorize"
    CAPTURE = "capture"
    VOID = "void"
    REFUND = "refund"
    CONFIRM = "confirm"


class TransactionError(Enum):
    """Represents a transaction error."""

    INCORRECT_NUMBER = "incorrect_number"
    INVALID_NUMBER = "invalid_number"
    INCORRECT_CVV = "incorrect_cvv"
    INVALID_CVV = "invalid_cvv"
    INCORRECT_ZIP = "incorrect_zip"
    INCORRECT_ADDRESS = "incorrect_address"
    INVALID_EXPIRY_DATE = "invalid_expiry_date"
    EXPIRED = "expired"
    PROCESSING_ERROR = "processing_error"
    DECLINED = "declined"


class TransactionKind:
    """Represents the type of a transaction.

    The following transactions types are possible:
    - AUTH - an amount reserved against the customer's funding source. Money
    does not change hands until the authorization is captured.
    - VOID - a cancellation of a pending authorization or capture.
    - CAPTURE - a transfer of the money that was reserved during the
    authorization stage.
    - REFUND - full or partial return of captured funds to the customer.
    """

    EXTERNAL = "external"
    AUTH = "auth"
    CAPTURE = "capture"
    CAPTURE_FAILED = "capture_failed"
    ACTION_TO_CONFIRM = "action_to_confirm"
    VOID = "void"
    PENDING = "pending"
    REFUND = "refund"
    REFUND_ONGOING = "refund_ongoing"
    REFUND_FAILED = "refund_failed"
    REFUND_REVERSED = "refund_reversed"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    # FIXME we could use another status like WAITING_FOR_AUTH for transactions
    # Which were authorized, but needs to be confirmed manually by staff
    # eg. Braintree with "submit_for_settlement" enabled
    CHOICES = [
        (EXTERNAL, "External reference"),
        (AUTH, "Authorization"),
        (PENDING, "Pending"),
        (ACTION_TO_CONFIRM, "Action to confirm"),
        (REFUND, "Refund"),
        (REFUND_ONGOING, "Refund in progress"),
        (CAPTURE, "Capture"),
        (VOID, "Void"),
        (CONFIRM, "Confirm"),
        (CANCEL, "Cancel"),
    ]


class ChargeStatus:
    """Represents possible statuses of a payment.

    The following statuses are possible:
    - NOT_CHARGED - no funds were take off the customer founding source yet.
    - PARTIALLY_CHARGED - funds were taken off the customer's funding source,
    partly covering the payment amount.
    - FULLY_CHARGED - funds were taken off the customer founding source,
    partly or completely covering the payment amount.
    - PARTIALLY_REFUNDED - part of charged funds were returned to the customer.
    - FULLY_REFUNDED - all charged funds were returned to the customer.
    """

    NOT_CHARGED = "not-charged"
    PENDING = "pending"
    PARTIALLY_CHARGED = "partially-charged"
    FULLY_CHARGED = "fully-charged"
    PARTIALLY_REFUNDED = "partially-refunded"
    FULLY_REFUNDED = "fully-refunded"
    REFUSED = "refused"
    CANCELLED = "cancelled"

    CHOICES = [
        (NOT_CHARGED, "Not charged"),
        (PENDING, "Pending"),
        (PARTIALLY_CHARGED, "Partially charged"),
        (FULLY_CHARGED, "Fully charged"),
        (PARTIALLY_REFUNDED, "Partially refunded"),
        (FULLY_REFUNDED, "Fully refunded"),
        (REFUSED, "Refused"),
        (CANCELLED, "Cancelled"),
    ]


class StorePaymentMethod:
    """Represents if and how a payment should be stored in a payment gateway.

    The following store types are possible:
    - ON_SESSION - the payment is stored only to be reused when
    the customer is present in the checkout flow
    - OFF_SESSION - the payment is stored to be reused even if
    the customer is absent
    - NONE - the payment is not stored.
    """

    ON_SESSION = "on_session"
    OFF_SESSION = "off_session"
    NONE = "none"

    CHOICES = [
        (ON_SESSION, "On session"),
        (OFF_SESSION, "Off session"),
        (NONE, "None"),
    ]


class TransactionAction:
    """Represents possible actions on payment transaction.

    The following actions are possible:
    CHARGE - Represents the charge action.
    REFUND - Represents a refund action.
    CANCEL - Represents a cancel action. Added in Saleor 3.12.
    """

    CHARGE = "charge"
    REFUND = "refund"
    CANCEL = "cancel"

    CHOICES = [
        (CHARGE, "Charge payment"),
        (REFUND, "Refund payment"),
        (CANCEL, "Cancel payment"),
    ]


class TransactionEventType:
    """Represents possible event types.

    Added in Saleor 3.12.

    The following types are possible:
    AUTHORIZATION_SUCCESS - represents success authorization.
    AUTHORIZATION_FAILURE - represents failure authorization.
    AUTHORIZATION_ADJUSTMENT - represents authorization adjustment.
    AUTHORIZATION_REQUEST - represents authorization request.
    AUTHORIZATION_ACTION_REQUIRED - represents authorization that needs
    additional actions from the customer.
    CHARGE_ACTION_REQUIRED - represents charge that needs
    additional actions from the customer.
    CHARGE_SUCCESS - represents success charge.
    CHARGE_FAILURE - represents failure charge.
    CHARGE_BACK - represents chargeback.
    CHARGE_REQUEST - represents charge request.
    REFUND_SUCCESS - represents success refund.
    REFUND_FAILURE - represents failure refund.
    REFUND_REVERSE - represents reverse refund.
    REFUND_REQUEST - represents refund request.
    CANCEL_SUCCESS - represents success cancel.
    CANCEL_FAILURE - represents failure cancel.
    CANCEL_REQUEST - represents cancel request.
    INFO - represents info event.
    """

    AUTHORIZATION_SUCCESS = "authorization_success"
    AUTHORIZATION_FAILURE = "authorization_failure"
    AUTHORIZATION_ADJUSTMENT = "authorization_adjustment"
    AUTHORIZATION_REQUEST = "authorization_request"
    AUTHORIZATION_ACTION_REQUIRED = "authorization_action_required"
    CHARGE_SUCCESS = "charge_success"
    CHARGE_FAILURE = "charge_failure"
    CHARGE_BACK = "charge_back"
    CHARGE_ACTION_REQUIRED = "charge_action_required"
    CHARGE_REQUEST = "charge_request"
    REFUND_SUCCESS = "refund_success"
    REFUND_FAILURE = "refund_failure"
    REFUND_REVERSE = "refund_reverse"
    REFUND_REQUEST = "refund_request"
    CANCEL_SUCCESS = "cancel_success"
    CANCEL_FAILURE = "cancel_failure"
    CANCEL_REQUEST = "cancel_request"
    INFO = "info"

    CHOICES = [
        (AUTHORIZATION_SUCCESS, "Represents success authorization"),
        (AUTHORIZATION_FAILURE, "Represents failure authorization"),
        (AUTHORIZATION_ADJUSTMENT, "Represents authorization adjustment"),
        (AUTHORIZATION_REQUEST, "Represents authorization request"),
        (
            AUTHORIZATION_ACTION_REQUIRED,
            "Represents additional actions required for authorization.",
        ),
        (CHARGE_ACTION_REQUIRED, "Represents additional actions required for charge."),
        (CHARGE_SUCCESS, "Represents success charge"),
        (CHARGE_FAILURE, "Represents failure charge"),
        (CHARGE_BACK, "Represents chargeback."),
        (CHARGE_REQUEST, "Represents charge request"),
        (REFUND_SUCCESS, "Represents success refund"),
        (REFUND_FAILURE, "Represents failure refund"),
        (REFUND_REVERSE, "Represents reverse refund"),
        (REFUND_REQUEST, "Represents refund request"),
        (CANCEL_SUCCESS, "Represents success cancel"),
        (CANCEL_FAILURE, "Represents failure cancel"),
        (CANCEL_REQUEST, "Represents cancel request"),
        (INFO, "Represents an info event"),
    ]


class TokenizedPaymentFlow:
    """Represents possible tokenized payment flows that can be used to process payment.

    The following flows are possible:
    INTERACTIVE - Payment method can be used for 1 click checkout - it's prefilled in
    checkout form (might require additional authentication from user)
    """

    INTERACTIVE = "interactive"

    CHOICES = [
        (INTERACTIVE, "Interactive"),
    ]
