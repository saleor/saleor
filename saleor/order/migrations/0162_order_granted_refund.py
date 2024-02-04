from decimal import Decimal

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0020_app_is_installed"),
        ("account", "0076_fill_empty_passwords"),
        ("order", "0161_merge_20221219_1838"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderGrantedRefund",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "amount_value",
                    models.DecimalField(
                        decimal_places=3, default=Decimal("0"), max_digits=12
                    ),
                ),
                ("currency", models.CharField(max_length=3)),
                ("reason", models.TextField(blank=True, default="")),
                (
                    "app",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="app.app",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="granted_refunds",
                        to="order.order",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="account.user",
                    ),
                ),
            ],
            options={
                "ordering": ("created_at", "id"),
            },
        ),
        migrations.AlterField(
            model_name="orderevent",
            name="type",
            field=models.CharField(
                choices=[
                    ("DRAFT_CREATED", "draft_created"),
                    ("DRAFT_CREATED_FROM_REPLACE", "draft_created_from_replace"),
                    ("ADDED_PRODUCTS", "added_products"),
                    ("REMOVED_PRODUCTS", "removed_products"),
                    ("PLACED", "placed"),
                    ("PLACED_FROM_DRAFT", "placed_from_draft"),
                    ("OVERSOLD_ITEMS", "oversold_items"),
                    ("CANCELED", "canceled"),
                    ("ORDER_MARKED_AS_PAID", "order_marked_as_paid"),
                    ("ORDER_FULLY_PAID", "order_fully_paid"),
                    ("ORDER_REPLACEMENT_CREATED", "order_replacement_created"),
                    ("ORDER_DISCOUNT_ADDED", "order_discount_added"),
                    (
                        "ORDER_DISCOUNT_AUTOMATICALLY_UPDATED",
                        "order_discount_automatically_updated",
                    ),
                    ("ORDER_DISCOUNT_UPDATED", "order_discount_updated"),
                    ("ORDER_DISCOUNT_DELETED", "order_discount_deleted"),
                    ("ORDER_LINE_DISCOUNT_UPDATED", "order_line_discount_updated"),
                    ("ORDER_LINE_DISCOUNT_REMOVED", "order_line_discount_removed"),
                    ("ORDER_LINE_PRODUCT_DELETED", "order_line_product_deleted"),
                    ("ORDER_LINE_VARIANT_DELETED", "order_line_variant_deleted"),
                    ("UPDATED_ADDRESS", "updated_address"),
                    ("EMAIL_SENT", "email_sent"),
                    ("CONFIRMED", "confirmed"),
                    ("PAYMENT_AUTHORIZED", "payment_authorized"),
                    ("PAYMENT_CAPTURED", "payment_captured"),
                    ("EXTERNAL_SERVICE_NOTIFICATION", "external_service_notification"),
                    ("PAYMENT_REFUNDED", "payment_refunded"),
                    ("PAYMENT_VOIDED", "payment_voided"),
                    ("PAYMENT_FAILED", "payment_failed"),
                    ("TRANSACTION_EVENT", "transaction_event"),
                    ("TRANSACTION_CHARGE_REQUESTED", "transaction_charge_requested"),
                    ("TRANSACTION_CAPTURE_REQUESTED", "transaction_capture_requested"),
                    ("TRANSACTION_REFUND_REQUESTED", "transaction_refund_requested"),
                    ("TRANSACTION_VOID_REQUESTED", "transaction_void_requested"),
                    ("TRANSACTION_CANCEL_REQUESTED", "transaction_cancel_requested"),
                    (
                        "TRANSACTION_MARK_AS_PAID_FAILED",
                        "transaction_mark_as_paid_failed",
                    ),
                    ("INVOICE_REQUESTED", "invoice_requested"),
                    ("INVOICE_GENERATED", "invoice_generated"),
                    ("INVOICE_UPDATED", "invoice_updated"),
                    ("INVOICE_SENT", "invoice_sent"),
                    ("FULFILLMENT_CANCELED", "fulfillment_canceled"),
                    ("FULFILLMENT_RESTOCKED_ITEMS", "fulfillment_restocked_items"),
                    ("FULFILLMENT_FULFILLED_ITEMS", "fulfillment_fulfilled_items"),
                    ("FULFILLMENT_REFUNDED", "fulfillment_refunded"),
                    ("FULFILLMENT_RETURNED", "fulfillment_returned"),
                    ("FULFILLMENT_REPLACED", "fulfillment_replaced"),
                    ("FULFILLMENT_AWAITS_APPROVAL", "fulfillment_awaits_approval"),
                    ("TRACKING_UPDATED", "tracking_updated"),
                    ("NOTE_ADDED", "note_added"),
                    ("OTHER", "other"),
                ],
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="authorize_status",
            field=models.CharField(
                choices=[
                    ("none", "The funds are not authorized"),
                    (
                        "partial",
                        "The funds that are authorized and charged don't cover fully "
                        "the order's total",
                    ),
                    (
                        "full",
                        "The funds that are authorized and charged fully cover the "
                        "order's total",
                    ),
                ],
                db_index=True,
                default="none",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="charge_status",
            field=models.CharField(
                choices=[
                    ("none", "The order is not charged."),
                    ("partial", "The order is partially charged"),
                    ("full", "The order is fully charged"),
                    ("overcharged", "The order is overcharged"),
                ],
                db_index=True,
                default="none",
                max_length=32,
            ),
        ),
    ]
