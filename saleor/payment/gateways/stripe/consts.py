PLUGIN_ID = "saleor.payments.stripe"
PLUGIN_NAME = "Stripe"
WEBHOOK_PATH = "webhooks/"

WEBHOOK_SUCCESS_EVENT = "payment_intent.succeeded"
WEBHOOK_PROCESSING_EVENT = "payment_intent.processing"
WEBHOOK_FAILED_EVENT = "payment_intent.payment_failed"
WEBHOOK_AUTHORIZED_EVENT = "payment_intent.amount_capturable_updated"
WEBHOOK_CANCELED_EVENT = "payment_intent.canceled"

WEBHOOK_REFUND_EVENT = "charge.refunded"


WEBHOOK_EVENTS = [
    WEBHOOK_SUCCESS_EVENT,
    WEBHOOK_PROCESSING_EVENT,
    WEBHOOK_FAILED_EVENT,
    WEBHOOK_AUTHORIZED_EVENT,
    WEBHOOK_CANCELED_EVENT,
    WEBHOOK_REFUND_EVENT,
]
METADATA_IDENTIFIER = "saleor-domain"

ACTION_REQUIRED_STATUSES = [
    "requires_payment_method",
    "requires_confirmation",
    "requires_action",
]

FAILED_STATUSES = ["requires_payment_method", "canceled"]

SUCCESS_STATUS = "succeeded"

PROCESSING_STATUS = "processing"

AUTHORIZED_STATUS = "requires_capture"

AUTOMATIC_CAPTURE_METHOD = "automatic"
MANUAL_CAPTURE_METHOD = "manual"

STRIPE_API_VERSION = "2020-08-27"
