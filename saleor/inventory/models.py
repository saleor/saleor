from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex
from django.db import models
from django.db.models import F, Q, Sum, Value
from django.db.models.fields import IntegerField
from django.db.models.functions import Coalesce, Greatest
from django.utils.timezone import now
from django_countries.fields import CountryField
from prices import Money

from ..app.models import App
from ..core.utils.json_serializer import CustomJsonEncoder
from ..product.models import ProductVariant
from ..warehouse.models import Warehouse
from . import (
    PurchaseOrderEvents,
    PurchaseOrderItemAdjustmentReason,
    PurchaseOrderItemStatus,
    PurchaseOrderStatus,
    ReceiptStatus,
)

"""
A PurchaseOrder is created when we confirm we will order some products from a supplier.
We create the corresponding PurchaseOrderItems at the same time.
We can add an Invoice using the Xero invoice id to a PurchaseOrder to get payment data

Stock must exist in a nonowned warehouse correlating to the supplier we buy the stock
from.

On confirmation of a purchase order stock is moved to owned warehouses and Orders that
are using stock from the nonowned warehouse are reallocated from the moved stock in FIFO
priority. Purchase order confirmation occurs _before_ products arrive in the destination warehouse.

When we allocate stock to orders from owned warehouses, we create AllocationSources and
update the POI quantity_allocated.

On Shipment arrival we create a Receipt. After receipt confirmation, we allocate
PurchaseOrderItemAdjustment ( POIA ) to account for changes in the quantity of stock
from this purchase order compared to what we expected.

Currently we don't track VAT (it is all reclaimed anyway). This means the cash flow
isn't fully accurate.

TODO: add a celery task to check the Stock is as expected every evening.
"""


class PurchaseOrder(models.Model):
    """Products come into owned warehouses through a PurchaseOrder.

    This is an order of goods from some supplier. One PurchaseOrder is one Invoice from a supplier.
    """

    # this must be a non-owned warehouse. We can't null this because stock must come from somewhere, and we expect that
    # the ProductVariants already exist for the units, which means that the variants
    # should all exist in a non-owned warehouse _before_ a deal is ingested.
    source_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.DO_NOTHING, related_name="source_purchase_orders"
    )

    # this has to be an owned warehouse
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.DO_NOTHING,
        related_name="destination_purchase_orders",
    )

    name = models.CharField(max_length=255, blank=True, default="")
    currency = models.CharField(max_length=3, blank=True, default="")

    status = models.CharField(
        max_length=32,
        choices=PurchaseOrderStatus.CHOICES,
        default=PurchaseOrderStatus.DRAFT,
    )

    auto_reallocate_variants = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PurchaseOrderRequestedAllocation(models.Model):
    """PORA for short. The allocations we want to confirm for this purchase order.

    We may not be able to confirm the entire allocation. Should only exist when PO has
    draft state.

    In order to confirm orders stock must move, via a PO, to an owned warehouse. We know
    how much stock a warehouse should confirm to an order by looking at the Allocations on
    the Order (which must be in the unconfirmed state).

    On confirmation we will only confirm stock from these Allocations, FIFO by order line
    creation time:
        for poi in PurchaseOrderItem:
            allocation_candidates = (
                PurchaseOrderRequestedAllocation.objects
                .filter(purchase_order=my_po)
                .order_by("allocation__order_line__created_at")
            )
            for pora in allocation_candidates:
                allocate_as_much_as_possible(pora)
                if poi exhausted: break
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="requested_allocations",
    )
    allocation = models.ForeignKey(
        "warehouse.Allocation",
        on_delete=models.CASCADE,
        related_name="purchase_order_requested_allocations",
    )

    class Meta:
        unique_together = [["purchase_order", "allocation"]]


class PurchaseOrderItemQuerySet(models.QuerySet):
    def annotate_available_quantity(self):
        """Annotate available_quantity in a single query.

        Calculates: quantity_ordered + processed_adjustments - quantity_allocated - quantity_fulfilled

        This eliminates N+1 queries when accessing available_quantity in loops.
        """
        return self.annotate(
            processed_adjustments=Coalesce(
                Sum(
                    "adjustments__quantity_change",
                    filter=Q(adjustments__processed_at__isnull=False),
                ),
                Value(0),
                output_field=IntegerField(),
            ),
            _available_quantity=Greatest(
                F("quantity_ordered")
                + F("processed_adjustments")
                - F("quantity_allocated")
                - F("quantity_fulfilled"),
                Value(0),
                output_field=IntegerField(),
            ),
        )


PurchaseOrderItemManager = models.Manager.from_queryset(PurchaseOrderItemQuerySet)


class PurchaseOrderItem(models.Model):
    """A variant + quantity on a PurchaseOrder. Like the invoice line item.

    This is not unique on the PurchaseOrder, ProductVariant which appears odd.
    We want to make an escape hatch for these 2 cases:
    1. A single purchase order item is in 2 different shipments
    2. A single purchase order item is for a different country of origin.

    """

    # lets keep this NOT unique on variant,order to account for country of origin
    # changes + different shipments
    order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="items"
    )
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="items"
    )
    quantity_ordered = models.PositiveIntegerField()
    # Tracks how much of this batch has been allocated to customer orders
    # via AllocationSource
    quantity_allocated = models.PositiveIntegerField(default=0)
    # Tracks how much of this batch has been fulfilled (shipped out)
    # via FulfillmentSource
    quantity_fulfilled = models.PositiveIntegerField(default=0)

    objects = PurchaseOrderItemManager()

    @property
    def available_quantity(self):
        """Amount available for allocation.

        Calculates: quantity_ordered + processed_adjustments - quantity_allocated - quantity_fulfilled

        Uses annotated value if available (from annotate_available_quantity()),
        otherwise queries database. Only processed adjustments (processed_at is set)
        are included in the calculation. This allows adjustments to be created but
        not applied until explicitly processed.
        """
        # Check if we have the annotated value from annotate_available_quantity()
        if hasattr(self, "_available_quantity"):
            return self._available_quantity

        # Fallback to query (for single-object access without annotation)
        from django.db.models import Sum

        processed_adjustments = (
            self.adjustments.filter(processed_at__isnull=False).aggregate(
                total=Sum("quantity_change")
            )["total"]
            or 0
        )

        base = self.quantity_ordered + processed_adjustments
        return max(0, base - self.quantity_allocated - self.quantity_fulfilled)

    @property
    def quantity_received(self):
        """Total quantity received across all receipt lines.

        Sums the quantity_received from all ReceiptLine records
        associated with this purchase order item.
        """
        from django.db.models import Sum

        total = self.receipt_lines.aggregate(total=Sum("quantity_received"))["total"]
        return total or 0

    @property
    def unit_price_amount(self):
        """Unit price per available unit after adjustments.

        For supplier credits (affects_payable=True): both cost and quantity adjust,
        so unit price remains constant.

        For losses we eat (affects_payable=False): only quantity decreases,
        making unit cost more expensive.
        """
        from django.db.models import Sum

        if self.quantity_ordered == 0 or self.total_price_amount is None:
            return 0

        base_unit_price = self.total_price_amount / self.quantity_ordered

        # Adjust COST only for supplier credits/charges (affects_payable)
        payable_adjustment = Decimal(
            self.adjustments.filter(
                affects_payable=True, processed_at__isnull=False
            ).aggregate(total=Sum("quantity_change"))["total"]
            or 0
        )
        adjusted_cost = self.total_price_amount + (payable_adjustment * base_unit_price)

        # Adjust QUANTITY for ALL processed adjustments (payable + non-payable)
        all_adjustments = (
            self.adjustments.filter(processed_at__isnull=False).aggregate(
                total=Sum("quantity_change")
            )["total"]
            or 0
        )
        adjusted_quantity = self.quantity_ordered + all_adjustments

        if adjusted_quantity > 0:
            return adjusted_cost / adjusted_quantity

        return base_unit_price

    @property
    def unit_price(self):
        """Unit price as Money object."""
        return Money(self.unit_price_amount, self.currency)

    total_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        null=True,
        blank=True,
        help_text="Total invoice amount. Null until set from price list.",
    )

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
        null=True,
        blank=True,
    )

    shipment = models.ForeignKey(
        "shipping.Shipment",
        on_delete=models.DO_NOTHING,
        related_name="purchase_order_items",
        null=True,
        blank=True,
    )

    country_of_origin = CountryField(null=True, blank=True)

    status = models.CharField(
        max_length=32,
        choices=PurchaseOrderItemStatus.CHOICES,
        default=PurchaseOrderItemStatus.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When status changed to CONFIRMED (ordered from supplier)",
    )

    def clean(self):
        from django.core.exceptions import ValidationError

        from ..shipping import ShipmentType

        super().clean()

        if self.shipment_id and self.shipment:
            if self.shipment.shipment_type != ShipmentType.INBOUND:
                raise ValidationError(
                    {
                        "shipment": (
                            f"Cannot link purchase order item to {self.shipment.shipment_type} shipment. "
                            "Purchase order items can only be linked to inbound shipments."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        if self.shipment_id:
            self.clean()
        super().save(*args, **kwargs)


class PurchaseOrderItemAdjustment(models.Model):
    """Audit trail for inventory adjustments (leakage).

    We create this whenever we identify a change in what we expected from
    available quantity compared to what we currently have now.

    Because we need to account for where all products come from, we track
    these changes on the POI, not the Stock.

    TODO: add something for affects_payable for whether we have got our refund from the
    supplier.

    Processing these is painful because we may have confirmed some orders!
    The possible outcomes:
    1. the good: we can handle the shortage by simply removing from unused quantity (unlikely as
    we are dropshippers and
    we dont tend to buy unpromised stock)
    2. the bad: we have to unconfirm some orders that have not been paid for due to
    shortage.
    3. the ugly: we have to refund some orders that have been paid due to the shortage

    """

    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name="adjustments",
        help_text="Which POI batch this adjustment applies to",
    )

    quantity_change = models.IntegerField(
        help_text="Change in quantity (negative for losses, positive for gains)"
    )

    reason = models.CharField(
        max_length=32,
        choices=PurchaseOrderItemAdjustmentReason.CHOICES,
        help_text="Why this adjustment was made",
    )

    affects_payable = models.BooleanField(
        default=False,
        help_text=(
            "True if supplier credits us for this adjustment "
            "(invoice variance, delivery short). "
            "False if we eat the loss (shrinkage, damage)."
        ),
    )

    notes = models.TextField(
        blank=True, help_text="Additional details about the adjustment"
    )

    # if we have handled the change in stock. For the cases where orders are unpaid this
    # is easy. It is much harder when they are not!
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this adjustment was processed (stock updated, allocations adjusted)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who recorded this adjustment",
    )

    @property
    def financial_impact(self):
        """Calculate the financial impact of this adjustment.

        Returns the cost impact in the POI's currency based on the original invoice unit price.
        Negative for losses, positive for gains.
        """
        poi = self.purchase_order_item
        original_unit_price = (
            poi.total_price_amount / poi.quantity_ordered
            if poi.quantity_ordered > 0 and poi.total_price_amount is not None
            else 0
        )
        return self.quantity_change * original_unit_price

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["purchase_order_item", "-created_at"]),
            models.Index(fields=["reason", "-created_at"]),
            models.Index(fields=["processed_at"]),
            models.Index(fields=["affects_payable", "-created_at"]),
        ]

    def __str__(self):
        direction = "loss" if self.quantity_change < 0 else "gain"
        return (
            f"POI #{self.purchase_order_item.id}: "
            f"{abs(self.quantity_change)} unit {direction} ({self.reason})"
        )


class Receipt(models.Model):
    """Document for receiving inbound shipments from suppliers.

    Tracks the physical receiving process for a shipment. When warehouse staff
    receive goods, they create a Receipt and add ReceiptLines as items are scanned.

    Workflow:
    1. Create Receipt for a Shipment (status=IN_PROGRESS)
    2. Add ReceiptLines as items are scanned/counted
    3. Complete Receipt → creates adjustments for discrepancies,
       sets Shipment.arrived_at, updates POI status to RECEIVED
    """

    shipment = models.OneToOneField(
        "shipping.Shipment",
        on_delete=models.CASCADE,
        related_name="receipt",
        help_text="Inbound shipment being received",
    )

    status = models.CharField(
        max_length=32,
        choices=ReceiptStatus.CHOICES,
        default=ReceiptStatus.IN_PROGRESS,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When receiving was completed and processed",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receipts_created",
        help_text="Warehouse staff who started receiving",
    )

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receipts_completed",
        help_text="Warehouse staff who completed receiving",
    )

    notes = models.TextField(
        blank=True, help_text="Additional notes about this receipt"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shipment", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"Receipt #{self.id} for Shipment #{self.shipment_id}"


class ReceiptLine(models.Model):
    """Individual line item in a goods receipt.

    Tracks what was actually received for each PurchaseOrderItem.
    Multiple ReceiptLines can exist for the same POI if items are
    scanned in separate batches during receiving.
    """

    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name="receipt_lines",
        help_text="Which POI this line receives against",
    )

    quantity_received = models.PositiveIntegerField(
        help_text="Quantity physically received in this receipt line"
    )

    received_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this specific item/batch was scanned",
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Warehouse staff who scanned this item",
    )

    notes = models.TextField(
        blank=True, help_text="Notes about this specific line (damage, etc.)"
    )

    class Meta:
        ordering = ["received_at"]
        indexes = [
            models.Index(fields=["receipt", "purchase_order_item"]),
            models.Index(fields=["received_at"]),
        ]

    def __str__(self):
        return (
            f"ReceiptLine: {self.quantity_received}x "
            f"{self.purchase_order_item.product_variant.sku}"
        )


class PurchaseOrderEvent(models.Model):
    """Audit trail for purchase order operations.

    Tracks all significant events during purchase order lifecycle including:
    - Order creation and confirmation
    - Items added/removed
    - Adjustments created and processed
    - Shipment assignments
    - Status changes
    """

    date = models.DateTimeField(default=now, editable=False, db_index=True)
    type = models.CharField(max_length=255, choices=PurchaseOrderEvents.CHOICES)

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        related_name="events",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Purchase order this event relates to",
    )

    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        related_name="events",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Specific POI this event relates to (optional)",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="User who triggered this event",
    )

    app = models.ForeignKey(
        App,
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="App that triggered this event",
    )

    parameters = models.JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)

    class Meta:
        ordering = ("date",)
        indexes = [
            BTreeIndex(fields=["date"], name="inventory_poevent_date_idx"),
            models.Index(fields=["purchase_order", "date"]),
            models.Index(fields=["purchase_order_item", "date"]),
            models.Index(fields=["type"]),
        ]

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"

    def __str__(self):
        if self.purchase_order_item:
            return f"PO Item #{self.purchase_order_item.id}: {self.get_type_display()}"
        return f"PO #{self.purchase_order_id}: {self.get_type_display()}"
