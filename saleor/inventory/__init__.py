class PurchaseOrderStatus:
    """Status of a purchase order through its lifecycle."""

    DRAFT = "draft"  # Being built; stock has not moved; PORAs may exist
    CONFIRMED = "confirmed"  # Committed to supplier; stock moved to owned warehouse
    PARTIALLY_RECEIVED = "partially_received"  # Some shipments arrived, not all
    RECEIVED = "received"  # All goods physically arrived; all receipts completed

    CHOICES = [
        (DRAFT, "Draft"),
        (CONFIRMED, "Confirmed"),
        (PARTIALLY_RECEIVED, "Partially Received"),
        (RECEIVED, "Received"),
    ]


class PurchaseOrderItemStatus:
    """Status of a purchase order item through its lifecycle."""

    DRAFT = "draft"  # Being entered into system
    CONFIRMED = "confirmed"  # Ordered from supplier, in transit
    RECEIVED = "received"  # Physically arrived in the warehouse
    CANCELLED = "cancelled"  # Cancelled
    REQUIRES_ATTENTION = "requires_attention"

    CHOICES = [
        (DRAFT, "Draft"),
        (CONFIRMED, "Confirmed"),
        (RECEIVED, "Received"),
        (CANCELLED, "Cancelled"),
        (REQUIRES_ATTENTION, "Requires Attention"),
    ]

    # Statuses that contribute to available inventory for allocation
    # Used when querying POIs for allocating sources to orders
    ACTIVE_STATUSES = [CONFIRMED, RECEIVED]

    # Statuses where stock is physically in the warehouse (for invariant checks)
    # Includes REQUIRES_ATTENTION because the stock is there, just unresolved
    STOCK_PRESENT_STATUSES = [CONFIRMED, RECEIVED, REQUIRES_ATTENTION]


class PurchaseOrderItemAdjustmentReason:
    """Reasons for post-receipt inventory adjustments."""

    SHRINKAGE_THEFT = "shrinkage_theft"
    SHRINKAGE_DAMAGE = "shrinkage_damage"
    SHRINKAGE_UNKNOWN = "shrinkage_unknown"

    CYCLE_COUNT_NEGATIVE = "cycle_count_neg"
    CYCLE_COUNT_POSITIVE = "cycle_count_pos"

    INVOICE_VARIANCE = "invoice_variance"
    DELIVERY_SHORT = "delivery_short"

    CHOICES = [
        (SHRINKAGE_THEFT, "Shrinkage - Theft"),
        (SHRINKAGE_DAMAGE, "Shrinkage - Damage"),
        (SHRINKAGE_UNKNOWN, "Shrinkage - Unknown"),
        (CYCLE_COUNT_NEGATIVE, "Cycle Count - Shortage Found"),
        (CYCLE_COUNT_POSITIVE, "Cycle Count - Excess Found"),
        (INVOICE_VARIANCE, "Invoice Variance"),
        (DELIVERY_SHORT, "Delivery Short"),
    ]


class ReceiptStatus:
    """Status of a goods receipt."""

    IN_PROGRESS = "in_progress"  # Currently receiving items
    COMPLETED = "completed"  # All items processed, shipment marked received
    CANCELLED = "cancelled"  # Receipt cancelled

    CHOICES = [
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]


class PurchaseOrderEvents:
    """Events that can occur during purchase order lifecycle."""

    CREATED = "created"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    ADJUSTMENT_CREATED = "adjustment_created"
    ADJUSTMENT_PROCESSED = "adjustment_processed"
    SHIPMENT_ASSIGNED = "shipment_assigned"
    NOTE_ADDED = "note_added"

    CHOICES = [
        (CREATED, "Purchase order created"),
        (CONFIRMED, "Purchase order confirmed with supplier"),
        (RECEIVED, "Goods received at warehouse"),
        (CANCELLED, "Purchase order cancelled"),
        (ITEM_ADDED, "Item added to purchase order"),
        (ITEM_REMOVED, "Item removed from purchase order"),
        (ADJUSTMENT_CREATED, "Inventory adjustment created"),
        (ADJUSTMENT_PROCESSED, "Inventory adjustment processed"),
        (SHIPMENT_ASSIGNED, "Shipment assigned"),
        (NOTE_ADDED, "Note added"),
    ]
