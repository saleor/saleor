from decimal import Decimal

from ..core.utils.apportionment import distribute_cost_proportionally
from ..core.utils.events import call_event
from ..invoice.models import Invoice, InvoiceEvents


def _line_total(stored_total, order_qty, quantity):
    if quantity == order_qty:
        return stored_total
    return (stored_total * quantity / order_qty).quantize(Decimal("0.01"))


def _line_gross(order_line, quantity):
    return _line_total(
        order_line.total_price_gross_amount, order_line.quantity, quantity
    )


def _line_net(order_line, quantity):
    return _line_total(order_line.total_price_net_amount, order_line.quantity, quantity)


def calculate_fulfillment_total(fulfillment):
    total = Decimal(0)
    for line in fulfillment.lines.all():
        total += _line_gross(line.order_line, line.quantity)
    return total


def _calculate_unfulfilled_weight(order, already_fulfilled_ids, new_fulfillments):
    """Calculate the gross value of order items not covered by any fulfillment."""
    fulfilled_qty_by_line: dict[int, int] = {}
    for f in order.fulfillments.all():
        if f.pk in already_fulfilled_ids:
            for fl in f.lines.all():
                fulfilled_qty_by_line[fl.order_line_id] = (
                    fulfilled_qty_by_line.get(fl.order_line_id, 0) + fl.quantity
                )
    for f in new_fulfillments:
        for fl in f.lines.all():
            fulfilled_qty_by_line[fl.order_line_id] = (
                fulfilled_qty_by_line.get(fl.order_line_id, 0) + fl.quantity
            )

    unfulfilled_total = Decimal(0)
    for line in order.lines.all():
        remaining_qty = line.quantity - fulfilled_qty_by_line.get(line.pk, 0)
        if remaining_qty > 0:
            unfulfilled_total += _line_gross(line, remaining_qty)
    return unfulfilled_total


def allocate_costs_to_fulfillments(order, new_fulfillments):
    """Apportion remaining deposit and shipping across new fulfillments.

    Subtracts already-allocated amounts from existing fulfillments, then uses
    Hamilton's method to split the remainder across the new batch.  A virtual
    weight for still-unfulfilled items ensures partial fulfillments only receive
    their proportional share.  Existing fulfillments are never modified.

    Sets ``deposit_allocated_amount`` and ``shipping_allocated_net_amount``
    on every fulfillment in *new_fulfillments* (caller must save).
    """
    currency = order.currency
    new_ids = {f.pk for f in new_fulfillments}

    already_allocated_deposit = Decimal(0)
    already_allocated_shipping_net = Decimal(0)
    existing_ids = set()
    for f in order.fulfillments.all():
        if f.pk not in new_ids:
            already_allocated_deposit += f.deposit_allocated_amount or Decimal(0)
            already_allocated_shipping_net += (
                f.shipping_allocated_net_amount or Decimal(0)
            )
            existing_ids.add(f.pk)

    weights = [calculate_fulfillment_total(f) for f in new_fulfillments]
    unfulfilled_weight = _calculate_unfulfilled_weight(
        order, existing_ids, new_fulfillments
    )
    weights_with_remainder = weights + [unfulfilled_weight]

    # --- deposit ---
    total_deposit = order.total_deposit_paid if order.deposit_required else Decimal(0)
    remaining_deposit = max(Decimal(0), total_deposit - already_allocated_deposit)
    deposit_shares = distribute_cost_proportionally(
        remaining_deposit, weights_with_remainder, currency
    )

    # --- shipping net ---
    shipping_net = order.shipping_price_net_amount or Decimal(0)
    remaining_shipping_net = max(
        Decimal(0), shipping_net - already_allocated_shipping_net
    )
    shipping_net_shares = distribute_cost_proportionally(
        remaining_shipping_net, weights_with_remainder, currency
    )

    # Discard the last entry (virtual unfulfilled bucket)
    for f, dep, ship_net in zip(
        new_fulfillments, deposit_shares[:-1], shipping_net_shares[:-1], strict=False
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
