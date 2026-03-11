from decimal import Decimal

from ..core.utils.apportionment import distribute_cost_proportionally
from ..core.utils.events import call_event
from ..invoice.models import Invoice, InvoiceEvents


def calculate_fulfillment_total(fulfillment):
    total = Decimal(0)
    for line in fulfillment.lines.all():
        order_line = line.order_line
        unit_price = order_line.unit_price_gross_amount
        total += unit_price * line.quantity
    return total


def allocate_costs_to_fulfillments(order, new_fulfillments):
    """Apportion remaining deposit and shipping across new fulfillments.

    Subtracts already-allocated amounts from existing fulfillments, then uses
    Hamilton's method to split the remainder across the new batch.  Existing
    fulfillments are never modified.

    Sets ``deposit_allocated_amount`` and ``shipping_allocated_net_amount``
    on every fulfillment in *new_fulfillments* (caller must save).
    """
    currency = order.currency
    new_ids = {f.pk for f in new_fulfillments}

    already_allocated_deposit = Decimal(0)
    already_allocated_shipping_net = Decimal(0)
    for f in order.fulfillments.all():
        if f.pk not in new_ids:
            already_allocated_deposit += f.deposit_allocated_amount or Decimal(0)
            already_allocated_shipping_net += (
                f.shipping_allocated_net_amount or Decimal(0)
            )

    weights = [calculate_fulfillment_total(f) for f in new_fulfillments]

    # --- deposit ---
    total_deposit = order.total_deposit_paid if order.deposit_required else Decimal(0)
    remaining_deposit = max(Decimal(0), total_deposit - already_allocated_deposit)
    deposit_shares = distribute_cost_proportionally(
        remaining_deposit, weights, currency
    )

    # --- shipping net ---
    shipping_net = order.shipping_price_net_amount or Decimal(0)
    remaining_shipping_net = max(
        Decimal(0), shipping_net - already_allocated_shipping_net
    )
    shipping_net_shares = distribute_cost_proportionally(
        remaining_shipping_net, weights, currency
    )

    for f, dep, ship_net in zip(
        new_fulfillments, deposit_shares, shipping_net_shares, strict=False
    ):
        f.deposit_allocated_amount = dep
        f.shipping_allocated_net_amount = ship_net


def generate_proforma_invoice(fulfillment, manager):
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
