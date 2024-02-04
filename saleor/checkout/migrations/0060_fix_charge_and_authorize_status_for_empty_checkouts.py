from decimal import Decimal

from django.db import migrations
from django.db.models.expressions import Exists, OuterRef
from prices import Money

# It takes less that a second to process the batch.
# The memory usage peak on celery worker was around 40MB.
BATCH_SIZE = 2000


def zero_money(currency):
    """Return a money object set to zero.

    This is a function used as a model's default.
    """
    return Money(0, currency)


def _update_charge_status(
    checkout,
    checkout_total_gross: Money,
    total_charged: Money,
    checkout_has_lines: bool,
):
    zero_money_amount = zero_money(checkout.currency)
    total_charged = max(zero_money_amount, total_charged)
    checkout_with_only_zero_price_lines = (
        checkout_has_lines and checkout_total_gross <= zero_money_amount
    )

    if total_charged <= zero_money_amount and checkout_with_only_zero_price_lines:
        checkout.charge_status = "full"
    elif total_charged <= zero_money_amount:
        checkout.charge_status = "none"
    elif total_charged < checkout_total_gross:
        checkout.charge_status = "partial"
    elif total_charged == checkout_total_gross:
        checkout.charge_status = "full"
    elif total_charged > checkout_total_gross:
        checkout.charge_status = "overcharged"
    else:
        checkout.charge_status = "none"


def _update_authorize_status(
    checkout,
    checkout_total_gross: Money,
    total_authorized: Money,
    total_charged: Money,
    checkout_has_lines: bool,
):
    total_covered = total_authorized + total_charged
    zero_money_amount = zero_money(checkout.currency)

    checkout_with_only_zero_price_lines = (
        checkout_has_lines and checkout_total_gross <= zero_money_amount
    )

    if total_covered <= zero_money_amount and checkout_with_only_zero_price_lines:
        checkout.authorize_status = "full"
    elif total_covered == zero_money_amount:
        checkout.authorize_status = "none"
    elif total_covered >= checkout_total_gross:
        checkout.authorize_status = "full"
    elif checkout_total_gross > total_covered > zero_money_amount:
        checkout.authorize_status = "partial"
    else:
        checkout.authorize_status = "none"


def _get_payment_amount_for_checkout(checkout_transactions, currency):
    total_charged_amount = zero_money(currency)
    total_authorized_amount = zero_money(currency)
    for transaction in checkout_transactions:
        total_authorized_amount += Money(transaction.authorized_value, currency)
        total_authorized_amount += Money(transaction.authorize_pending_value, currency)

        total_charged_amount += Money(transaction.charged_value, currency)
        total_charged_amount += Money(transaction.charge_pending_value, currency)
    return total_authorized_amount, total_charged_amount


def update_checkout_payment_statuses(
    checkout,
    checkout_total_gross: Money,
    checkout_has_lines: bool,
    checkout_transactions,
):
    total_authorized_amount, total_charged_amount = _get_payment_amount_for_checkout(
        checkout_transactions, checkout.currency
    )
    _update_authorize_status(
        checkout,
        checkout_total_gross,
        total_authorized_amount,
        total_charged_amount,
        checkout_has_lines,
    )
    _update_charge_status(
        checkout, checkout_total_gross, total_charged_amount, checkout_has_lines
    )


def fix_statuses_for_batch_of_empty_checkouts(
    Checkout, empty_checkouts_fully_charged_and_authorized_ids
):
    checkouts = Checkout.objects.filter(
        pk__in=empty_checkouts_fully_charged_and_authorized_ids
    ).prefetch_related("payment_transactions")
    checkouts_to_update = []
    for checkout in checkouts:
        update_checkout_payment_statuses(
            checkout,
            Money(checkout.total_gross_amount, checkout.currency),
            False,
            checkout.payment_transactions.all(),
        )
        checkouts_to_update.append(checkout)
    Checkout.objects.bulk_update(
        checkouts_to_update, ["authorize_status", "charge_status"]
    )


def fix_charge_status_for_empty_checkouts(apps, _schema_editor):
    Checkout = apps.get_model("checkout", "Checkout")
    CheckoutLine = apps.get_model("checkout", "CheckoutLine")

    while True:
        empty_checkouts_fully_charged_and_authorized_ids = Checkout.objects.filter(
            ~Exists(CheckoutLine.objects.filter(checkout_id=OuterRef("pk"))),
            charge_status="full",
            authorize_status="full",
            total_gross_amount__lte=Decimal(0),
        ).values_list("pk", flat=True)[:BATCH_SIZE]

        if not empty_checkouts_fully_charged_and_authorized_ids:
            break
        fix_statuses_for_batch_of_empty_checkouts(
            Checkout, empty_checkouts_fully_charged_and_authorized_ids
        )


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0059_merge_0058"),
        ("payment", "0049_auto_20230322_0634"),
    ]
    operations = [
        migrations.RunPython(
            fix_charge_status_for_empty_checkouts,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
