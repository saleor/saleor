from __future__ import absolute_import, division, print_function

import functools
import hmac
import io
import logging
import sys
import os
import re

import stripe
from stripe import six
from stripe.six.moves.urllib.parse import parse_qsl


STRIPE_LOG = os.environ.get("STRIPE_LOG")

logger = logging.getLogger("stripe")

__all__ = [
    "io",
    "parse_qsl",
    "utf8",
    "log_info",
    "log_debug",
    "dashboard_link",
    "logfmt",
]


def utf8(value):
    if six.PY2 and isinstance(value, six.text_type):
        return value.encode("utf-8")
    else:
        return value


def is_appengine_dev():
    return "APPENGINE_RUNTIME" in os.environ and "Dev" in os.environ.get(
        "SERVER_SOFTWARE", ""
    )


def _console_log_level():
    if stripe.log in ["debug", "info"]:
        return stripe.log
    elif STRIPE_LOG in ["debug", "info"]:
        return STRIPE_LOG
    else:
        return None


def log_debug(message, **params):
    msg = logfmt(dict(message=message, **params))
    if _console_log_level() == "debug":
        print(msg, file=sys.stderr)
    logger.debug(msg)


def log_info(message, **params):
    msg = logfmt(dict(message=message, **params))
    if _console_log_level() in ["debug", "info"]:
        print(msg, file=sys.stderr)
    logger.info(msg)


def _test_or_live_environment():
    if stripe.api_key is None:
        return
    match = re.match(r"sk_(live|test)_", stripe.api_key)
    if match is None:
        return
    return match.groups()[0]


def dashboard_link(request_id):
    return "https://dashboard.stripe.com/{env}/logs/{reqid}".format(
        env=_test_or_live_environment() or "test", reqid=request_id
    )


def logfmt(props):
    def fmt(key, val):
        # Handle case where val is a bytes or bytesarray
        if six.PY3 and hasattr(val, "decode"):
            val = val.decode("utf-8")
        # Check if val is already a string to avoid re-encoding into
        # ascii. Since the code is sent through 2to3, we can't just
        # use unicode(val, encoding='utf8') since it will be
        # translated incorrectly.
        if not isinstance(val, six.string_types):
            val = six.text_type(val)
        if re.search(r"\s", val):
            val = repr(val)
        # key should already be a string
        if re.search(r"\s", key):
            key = repr(key)
        return u"{key}={val}".format(key=key, val=val)

    return u" ".join([fmt(key, val) for key, val in sorted(props.items())])


# Borrowed from Django's source code
if hasattr(hmac, "compare_digest"):
    # Prefer the stdlib implementation, when available.
    def secure_compare(val1, val2):
        return hmac.compare_digest(utf8(val1), utf8(val2))


else:

    def secure_compare(val1, val2):
        """
        Returns True if the two strings are equal, False otherwise.
        The time taken is independent of the number of characters that match.
        For the sake of simplicity, this function executes in constant time
        only when the two strings have the same length. It short-circuits when
        they have different lengths.
        """
        val1, val2 = utf8(val1), utf8(val2)
        if len(val1) != len(val2):
            return False
        result = 0
        if six.PY3 and isinstance(val1, bytes) and isinstance(val2, bytes):
            for x, y in zip(val1, val2):
                result |= x ^ y
        else:
            for x, y in zip(val1, val2):
                result |= ord(x) ^ ord(y)
        return result == 0


OBJECT_CLASSES = {}


def load_object_classes():
    # This is here to avoid a circular dependency
    from stripe import api_resources

    global OBJECT_CLASSES

    OBJECT_CLASSES = {
        # data structures
        api_resources.ListObject.OBJECT_NAME: api_resources.ListObject,
        # business objects
        api_resources.Account.OBJECT_NAME: api_resources.Account,
        api_resources.AccountLink.OBJECT_NAME: api_resources.AccountLink,
        api_resources.AlipayAccount.OBJECT_NAME: api_resources.AlipayAccount,
        api_resources.ApplePayDomain.OBJECT_NAME: api_resources.ApplePayDomain,
        api_resources.ApplicationFee.OBJECT_NAME: api_resources.ApplicationFee,
        api_resources.ApplicationFeeRefund.OBJECT_NAME: api_resources.ApplicationFeeRefund,
        api_resources.Balance.OBJECT_NAME: api_resources.Balance,
        api_resources.BalanceTransaction.OBJECT_NAME: api_resources.BalanceTransaction,
        api_resources.BankAccount.OBJECT_NAME: api_resources.BankAccount,
        api_resources.BitcoinReceiver.OBJECT_NAME: api_resources.BitcoinReceiver,
        api_resources.BitcoinTransaction.OBJECT_NAME: api_resources.BitcoinTransaction,
        api_resources.Card.OBJECT_NAME: api_resources.Card,
        api_resources.Charge.OBJECT_NAME: api_resources.Charge,
        api_resources.checkout.Session.OBJECT_NAME: api_resources.checkout.Session,
        api_resources.CountrySpec.OBJECT_NAME: api_resources.CountrySpec,
        api_resources.Coupon.OBJECT_NAME: api_resources.Coupon,
        api_resources.CreditNote.OBJECT_NAME: api_resources.CreditNote,
        api_resources.Customer.OBJECT_NAME: api_resources.Customer,
        api_resources.Dispute.OBJECT_NAME: api_resources.Dispute,
        api_resources.EphemeralKey.OBJECT_NAME: api_resources.EphemeralKey,
        api_resources.Event.OBJECT_NAME: api_resources.Event,
        api_resources.ExchangeRate.OBJECT_NAME: api_resources.ExchangeRate,
        api_resources.File.OBJECT_NAME: api_resources.File,
        api_resources.File.OBJECT_NAME_ALT: api_resources.File,
        api_resources.FileLink.OBJECT_NAME: api_resources.FileLink,
        api_resources.Invoice.OBJECT_NAME: api_resources.Invoice,
        api_resources.InvoiceItem.OBJECT_NAME: api_resources.InvoiceItem,
        api_resources.InvoiceLineItem.OBJECT_NAME: api_resources.InvoiceLineItem,
        api_resources.IssuerFraudRecord.OBJECT_NAME: api_resources.IssuerFraudRecord,
        api_resources.issuing.Authorization.OBJECT_NAME: api_resources.issuing.Authorization,
        api_resources.issuing.Card.OBJECT_NAME: api_resources.issuing.Card,
        api_resources.issuing.CardDetails.OBJECT_NAME: api_resources.issuing.CardDetails,
        api_resources.issuing.Cardholder.OBJECT_NAME: api_resources.issuing.Cardholder,
        api_resources.issuing.Dispute.OBJECT_NAME: api_resources.issuing.Dispute,
        api_resources.issuing.Transaction.OBJECT_NAME: api_resources.issuing.Transaction,
        api_resources.LoginLink.OBJECT_NAME: api_resources.LoginLink,
        api_resources.Order.OBJECT_NAME: api_resources.Order,
        api_resources.OrderReturn.OBJECT_NAME: api_resources.OrderReturn,
        api_resources.PaymentIntent.OBJECT_NAME: api_resources.PaymentIntent,
        api_resources.PaymentMethod.OBJECT_NAME: api_resources.PaymentMethod,
        api_resources.Payout.OBJECT_NAME: api_resources.Payout,
        api_resources.Person.OBJECT_NAME: api_resources.Person,
        api_resources.Plan.OBJECT_NAME: api_resources.Plan,
        api_resources.Product.OBJECT_NAME: api_resources.Product,
        api_resources.radar.ValueList.OBJECT_NAME: api_resources.radar.ValueList,
        api_resources.radar.ValueListItem.OBJECT_NAME: api_resources.radar.ValueListItem,
        api_resources.Recipient.OBJECT_NAME: api_resources.Recipient,
        api_resources.RecipientTransfer.OBJECT_NAME: api_resources.RecipientTransfer,
        api_resources.Refund.OBJECT_NAME: api_resources.Refund,
        api_resources.reporting.ReportRun.OBJECT_NAME: api_resources.reporting.ReportRun,
        api_resources.reporting.ReportType.OBJECT_NAME: api_resources.reporting.ReportType,
        api_resources.Reversal.OBJECT_NAME: api_resources.Reversal,
        api_resources.Review.OBJECT_NAME: api_resources.Review,
        api_resources.sigma.ScheduledQueryRun.OBJECT_NAME: api_resources.sigma.ScheduledQueryRun,
        api_resources.SKU.OBJECT_NAME: api_resources.SKU,
        api_resources.Source.OBJECT_NAME: api_resources.Source,
        api_resources.SourceTransaction.OBJECT_NAME: api_resources.SourceTransaction,
        api_resources.Subscription.OBJECT_NAME: api_resources.Subscription,
        api_resources.SubscriptionItem.OBJECT_NAME: api_resources.SubscriptionItem,
        api_resources.SubscriptionSchedule.OBJECT_NAME: api_resources.SubscriptionSchedule,
        api_resources.SubscriptionScheduleRevision.OBJECT_NAME: api_resources.SubscriptionScheduleRevision,
        api_resources.TaxId.OBJECT_NAME: api_resources.TaxId,
        api_resources.TaxRate.OBJECT_NAME: api_resources.TaxRate,
        api_resources.ThreeDSecure.OBJECT_NAME: api_resources.ThreeDSecure,
        api_resources.Token.OBJECT_NAME: api_resources.Token,
        api_resources.Topup.OBJECT_NAME: api_resources.Topup,
        api_resources.Transfer.OBJECT_NAME: api_resources.Transfer,
        api_resources.UsageRecord.OBJECT_NAME: api_resources.UsageRecord,
        api_resources.UsageRecordSummary.OBJECT_NAME: api_resources.UsageRecordSummary,
        api_resources.WebhookEndpoint.OBJECT_NAME: api_resources.WebhookEndpoint,
        api_resources.terminal.Location.OBJECT_NAME: api_resources.terminal.Location,
        api_resources.terminal.ConnectionToken.OBJECT_NAME: api_resources.terminal.ConnectionToken,
        api_resources.terminal.Reader.OBJECT_NAME: api_resources.terminal.Reader,
    }


def convert_to_stripe_object(
    resp, api_key=None, stripe_version=None, stripe_account=None
):
    global OBJECT_CLASSES

    if len(OBJECT_CLASSES) == 0:
        load_object_classes()
    types = OBJECT_CLASSES.copy()

    # If we get a StripeResponse, we'll want to return a
    # StripeObject with the last_response field filled out with
    # the raw API response information
    stripe_response = None

    if isinstance(resp, stripe.stripe_response.StripeResponse):
        stripe_response = resp
        resp = stripe_response.data

    if isinstance(resp, list):
        return [
            convert_to_stripe_object(
                i, api_key, stripe_version, stripe_account
            )
            for i in resp
        ]
    elif isinstance(resp, dict) and not isinstance(
        resp, stripe.stripe_object.StripeObject
    ):
        resp = resp.copy()
        klass_name = resp.get("object")
        if isinstance(klass_name, six.string_types):
            klass = types.get(klass_name, stripe.stripe_object.StripeObject)
        else:
            klass = stripe.stripe_object.StripeObject

        return klass.construct_from(
            resp,
            api_key,
            stripe_version=stripe_version,
            stripe_account=stripe_account,
            last_response=stripe_response,
        )
    else:
        return resp


def convert_to_dict(obj):
    """Converts a StripeObject back to a regular dict.

    Nested StripeObjects are also converted back to regular dicts.

    :param obj: The StripeObject to convert.

    :returns: The StripeObject as a dict.
    """
    if isinstance(obj, list):
        return [convert_to_dict(i) for i in obj]
    # This works by virtue of the fact that StripeObjects _are_ dicts. The dict
    # comprehension returns a regular dict and recursively applies the
    # conversion to each value.
    elif isinstance(obj, dict):
        return {k: convert_to_dict(v) for k, v in six.iteritems(obj)}
    else:
        return obj


def populate_headers(idempotency_key):
    if idempotency_key is not None:
        return {"Idempotency-Key": idempotency_key}
    return None


class class_method_variant(object):
    def __init__(self, class_method_name):
        self.class_method_name = class_method_name

    def __call__(self, method):
        self.method = method
        return self

    def __get__(self, obj=None, objtype=None):
        @functools.wraps(self.method)
        def _wrapper(*args, **kwargs):
            if obj is not None:
                return self.method(obj, *args, **kwargs)
            else:
                class_method = getattr(objtype, self.class_method_name)
                return class_method(*args, **kwargs)

        return _wrapper
