from decimal import Decimal

from ..core.utils.events import call_event
from ..invoice.models import Invoice, InvoiceEvents

TWO_DP = Decimal("0.01")


def _is_order_fully_fulfilled(order) -> bool:
    return all(line.quantity_unfulfilled == 0 for line in order.lines.all())


def calculate_deposit_allocation(order, fulfillment_total):
    if not order.deposit_required:
        return Decimal(0)

    total_deposit_paid = order.total_deposit_paid
    if not total_deposit_paid:
        return Decimal(0)

    order_total = order.total_gross_amount
    if order_total == 0:
        return Decimal(0)

    already_allocated = sum(
        f.deposit_allocated_amount or Decimal(0) for f in order.fulfillments.all()
    )
    remaining_deposit = max(
        Decimal(0), (total_deposit_paid - already_allocated).quantize(TWO_DP)
    )

    if _is_order_fully_fulfilled(order):
        return remaining_deposit

    proportional_share = (
        fulfillment_total * total_deposit_paid / order_total
    ).quantize(TWO_DP)
    return min(remaining_deposit, proportional_share)


def calculate_proportional_shipping(
    shipping_amount, fulfillment_lines_total, order_lines_total
):
    """Calculate this fulfillment's proportional share of order shipping cost.

    Splits shipping by the fulfillment's share of the total order line value so that
    shipping is charged exactly once across all partial fulfillments.

    Args:
        shipping_amount: Full order shipping cost (gross or net)
        fulfillment_lines_total: Gross value of lines in this fulfillment
        order_lines_total: Gross value of all order lines

    Returns:
        Decimal: Proportional shipping amount (unrounded)

    """
    if not order_lines_total:
        return Decimal(0)
    return shipping_amount * fulfillment_lines_total / order_lines_total


def calculate_fulfillment_total(fulfillment):
    """Calculate total value of a fulfillment.

    Args:
        fulfillment: Fulfillment instance with lines

    Returns:
        Decimal: Total gross amount of fulfillment

    """
    total = Decimal(0)
    for line in fulfillment.lines.all():
        order_line = line.order_line
        unit_price = order_line.unit_price_gross_amount
        total += unit_price * line.quantity

    return total


def generate_proforma_invoice(fulfillment, manager):
    """Generate proforma invoice for a fulfillment and trigger webhook.

    Args:
        fulfillment: Fulfillment instance
        manager: PluginsManager for webhook triggering

    Returns:
        Invoice: Created proforma invoice

    """
    from ..invoice import InvoiceType

    order = fulfillment.order

    invoice = Invoice.objects.create(
        order=order,
        fulfillment=fulfillment,
        type=InvoiceType.PROFORMA,
        number=None,
        created=fulfillment.created_at,
    )

    invoice.events.create(
        type=InvoiceEvents.REQUESTED,
        user=None,
        parameters={"invoice_type": InvoiceType.PROFORMA},
    )

    call_event(manager.fulfillment_proforma_invoice_generated, fulfillment, invoice)

    return invoice
