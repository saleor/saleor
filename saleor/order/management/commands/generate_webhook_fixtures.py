r"""Generate webhook fixture files by rendering live subscription payloads.

Renders each sync webhook subscription (using the exact query from an app manifest)
against synthetic DB objects, then dumps the results as JSON files.

A temporary app is created with exactly the permissions declared in the manifest,
so fixture generation reflects the real permission context — no more, no less.
Any fields that would fail in production due to missing permissions will fail here too.

These fixtures are committed to the repo and used by downstream app test suites to
verify that their webhook handlers correctly process the payloads Saleor actually sends.

Usage:
    # From a local file
    uv run python manage.py generate_webhook_fixtures \\
        --manifest ../dirac/applications/saleor_xero_integration/manifest.json \\
        --output saleor/graphql/order/tests/e2e/xero_contracts/

    # From a running app
    uv run python manage.py generate_webhook_fixtures \\
        --manifest http://localhost:8086/manifest.json \\
        --output saleor/graphql/order/tests/e2e/xero_contracts/
"""

import json
import urllib.request
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ....app.models import App
from ....channel.models import Channel
from ....graphql.webhook.subscription_payload import (
    generate_payload_from_subscription,
    initialize_request,
)
from ....order import OrderOrigin, OrderStatus
from ....order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType


class _Rollback(Exception):
    pass


# ---------------------------------------------------------------------------
# Registry — add an entry here for every sync event in any manifest.
# Unregistered events cause the command to fail loudly.
# ---------------------------------------------------------------------------


def _gen_order_confirmed(query, output_dir, channel, request, stdout):
    payload = None
    try:
        with transaction.atomic():
            order = _make_order(channel)
            variant = _make_product_variant_with_code("FIXTURE-CODE")
            OrderLine.objects.create(
                order=order,
                variant=variant,
                product_name="Fixture Widget",
                variant_name="Standard",
                product_sku="FIXTURE-001",
                quantity=5,
                currency=channel.currency_code,
                unit_price_net_amount=Decimal("50.00"),
                unit_price_gross_amount=Decimal("60.00"),
                undiscounted_unit_price_net_amount=Decimal("50.00"),
                undiscounted_unit_price_gross_amount=Decimal("60.00"),
                base_unit_price_amount=Decimal("50.00"),
                total_price_net_amount=Decimal("250.00"),
                total_price_gross_amount=Decimal("300.00"),
                undiscounted_total_price_net_amount=Decimal("250.00"),
                undiscounted_total_price_gross_amount=Decimal("300.00"),
                unit_discount_amount=Decimal(0),
                is_shipping_required=True,
                is_gift_card=False,
                xero_tax_code="RROUTPUT",
            )
            payload = generate_payload_from_subscription(
                event_type=WebhookEventSyncType.XERO_ORDER_CONFIRMED,
                subscribable_object=order,
                subscription_query=query,
                request=request,
            )
            raise _Rollback()
    except _Rollback:
        pass
    _write(output_dir, "xero_order_confirmed.json", payload, stdout)


def _gen_fulfillment_created(query, output_dir, channel, request, stdout):
    payload = None
    try:
        with transaction.atomic():
            order = _make_order(channel)
            order.shipping_price_net_amount = Decimal("20.00")
            order.shipping_price_gross_amount = Decimal("24.00")
            order.save(
                update_fields=[
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                ]
            )

            variant = _make_product_variant_with_code("FIXTURE-CODE")
            order_line = OrderLine.objects.create(
                order=order,
                variant=variant,
                product_name="Fixture Widget",
                variant_name="Standard",
                product_sku="FIXTURE-001",
                quantity=10,
                currency=channel.currency_code,
                unit_price_net_amount=Decimal("25.00"),
                unit_price_gross_amount=Decimal("30.00"),
                undiscounted_unit_price_net_amount=Decimal("25.00"),
                undiscounted_unit_price_gross_amount=Decimal("30.00"),
                base_unit_price_amount=Decimal("25.00"),
                total_price_net_amount=Decimal("250.00"),
                total_price_gross_amount=Decimal("300.00"),
                undiscounted_total_price_net_amount=Decimal("250.00"),
                undiscounted_total_price_gross_amount=Decimal("300.00"),
                unit_discount_amount=Decimal(0),
                is_shipping_required=True,
                is_gift_card=False,
                xero_tax_code="RROUTPUT",
            )
            fulfillment = Fulfillment.objects.create(
                order=order,
                deposit_allocated_amount=Decimal("50.00"),
            )
            FulfillmentLine.objects.create(
                fulfillment=fulfillment,
                order_line=order_line,
                quantity=10,
            )
            payload = generate_payload_from_subscription(
                event_type=WebhookEventSyncType.XERO_FULFILLMENT_CREATED,
                subscribable_object=fulfillment,
                subscription_query=query,
                request=request,
            )
            raise _Rollback()
    except _Rollback:
        pass
    _write(output_dir, "xero_fulfillment_created.json", payload, stdout)


def _gen_list_bank_accounts(query, output_dir, channel, request, stdout):
    _write(output_dir, "xero_list_bank_accounts.json", {"domain": channel.slug}, stdout)


def _gen_list_tax_codes(query, output_dir, channel, request, stdout):
    _write(output_dir, "xero_list_tax_codes.json", {"domain": channel.slug}, stdout)


def _gen_check_prepayment_status(query, output_dir, channel, request, stdout):
    _write(
        output_dir,
        "xero_check_prepayment_status.json",
        {
            "prepaymentId": "00000000-0000-0000-0000-000000000000",
            "xeroContactId": "00000000-0000-0000-0000-000000000001",
        },
        stdout,
    )


def _gen_list_payments(query, output_dir, channel, request, stdout):
    _write(
        output_dir,
        "xero_list_payments.json",
        {
            "contactId": "00000000-0000-0000-0000-000000000000",
            "email": "fixture@example.com",
        },
        stdout,
    )


def _gen_xero_fulfillment_approved(query, output_dir, channel, request, stdout):
    from ....payment import ChargeStatus
    from ....payment.models import Payment

    payload = None
    try:
        with transaction.atomic():
            order = _make_order(channel)
            order.status = OrderStatus.UNFULFILLED
            order.shipping_price_net_amount = Decimal("20.00")
            order.shipping_price_gross_amount = Decimal("24.00")
            order.shipping_tax_rate = Decimal("0.20")
            order.save(
                update_fields=[
                    "status",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "shipping_tax_rate",
                ]
            )

            variant = _make_product_variant_with_code("FIXTURE-CODE")
            order_line = OrderLine.objects.create(
                order=order,
                variant=variant,
                product_name="Fixture Widget",
                variant_name="Standard",
                product_sku="FIXTURE-001",
                quantity=10,
                currency=channel.currency_code,
                unit_price_net_amount=Decimal("25.00"),
                unit_price_gross_amount=Decimal("30.00"),
                undiscounted_unit_price_net_amount=Decimal("25.00"),
                undiscounted_unit_price_gross_amount=Decimal("30.00"),
                base_unit_price_amount=Decimal("25.00"),
                total_price_net_amount=Decimal("250.00"),
                total_price_gross_amount=Decimal("300.00"),
                undiscounted_total_price_net_amount=Decimal("250.00"),
                undiscounted_total_price_gross_amount=Decimal("300.00"),
                unit_discount_amount=Decimal(0),
                is_shipping_required=True,
                is_gift_card=False,
                tax_rate=Decimal("0.20"),
                xero_tax_code="RROUTPUT",
            )

            fulfillment = Fulfillment.objects.create(
                order=order,
                deposit_allocated_amount=Decimal("90.00"),
            )
            FulfillmentLine.objects.create(
                fulfillment=fulfillment,
                order_line=order_line,
                quantity=10,
            )

            Payment.objects.create(
                gateway="xero",
                order=order,
                fulfillment=None,
                currency=channel.currency_code,
                total=Decimal("90.00"),
                captured_amount=Decimal("90.00"),
                charge_status=ChargeStatus.FULLY_CHARGED,
                psp_reference="00000000-0000-0000-0000-deposit-0001",
                is_active=True,
            )
            Payment.objects.create(
                gateway="xero",
                order=order,
                fulfillment=fulfillment,
                currency=channel.currency_code,
                total=Decimal("234.00"),
                captured_amount=Decimal("234.00"),
                charge_status=ChargeStatus.FULLY_CHARGED,
                psp_reference="00000000-0000-0000-0000-proforma-001",
                is_active=True,
            )

            payload = generate_payload_from_subscription(
                event_type=WebhookEventSyncType.XERO_FULFILLMENT_APPROVED,
                subscribable_object=fulfillment,
                subscription_query=query,
                request=request,
            )
            raise _Rollback()
    except _Rollback:
        pass
    _write(output_dir, "xero_fulfillment_approved.json", payload, stdout)


def _gen_customer_created(query, output_dir, channel, request, stdout):
    payload = None
    try:
        with transaction.atomic():
            from ....account.models import Address, User

            address = Address.objects.create(
                first_name="Fixture",
                last_name="User",
                company_name="Fixture Ltd",
                street_address_1="1 Test Street",
                city="London",
                postal_code="EC1A 1BB",
                country="GB",
            )
            user = User.objects.create_user(
                email="fixture@example.com",
                first_name="Fixture",
                last_name="User",
                default_billing_address=address,
                private_metadata={
                    "xeroContactId": "00000000-0000-0000-0000-000000000000"
                },
            )
            payload = generate_payload_from_subscription(
                event_type=WebhookEventAsyncType.CUSTOMER_CREATED,
                subscribable_object=user,
                subscription_query=query,
                request=request,
            )
            raise _Rollback()
    except _Rollback:
        pass
    _write(output_dir, "customer_created.json", payload, stdout)


EVENT_GENERATORS = {
    "XERO_ORDER_CONFIRMED": _gen_order_confirmed,
    "XERO_FULFILLMENT_CREATED": _gen_fulfillment_created,
    "XERO_FULFILLMENT_APPROVED": _gen_xero_fulfillment_approved,
    "XERO_LIST_BANK_ACCOUNTS": _gen_list_bank_accounts,
    "XERO_LIST_TAX_CODES": _gen_list_tax_codes,
    "XERO_CHECK_PREPAYMENT_STATUS": _gen_check_prepayment_status,
    "XERO_LIST_PAYMENTS": _gen_list_payments,
    "CUSTOMER_CREATED": _gen_customer_created,
}


class Command(BaseCommand):
    help = "Generate webhook fixture files from live subscription rendering"

    def add_arguments(self, parser):
        parser.add_argument(
            "--manifest",
            required=True,
            help="Path or URL to a Saleor app manifest.json",
        )
        parser.add_argument(
            "--output",
            default="saleor/graphql/order/tests/e2e/xero_contracts",
            help="Directory to write fixture files into",
        )

    def handle(self, *args, **options):
        manifest = _load_manifest(options["manifest"])
        output_dir = Path(options["output"])
        output_dir.mkdir(parents=True, exist_ok=True)

        channel = Channel.objects.first()
        if not channel:
            raise CommandError("No channel found — run with a populated database")

        # Create a temporary app with exactly the manifest permissions.
        # This mirrors the real production context — no more, no less.
        app = _create_temp_app(manifest)
        try:
            request = initialize_request(app=app)
            for webhook in manifest.get("webhooks", []):
                all_events = webhook.get("syncEvents", []) + webhook.get(
                    "asyncEvents", []
                )
                for event_name in all_events:
                    generator = EVENT_GENERATORS.get(event_name)
                    if generator is None:
                        raise CommandError(
                            f"No fixture generator registered for event "
                            f"{event_name!r}. Add one to EVENT_GENERATORS."
                        )
                    generator(
                        webhook["query"], output_dir, channel, request, self.stdout
                    )
        finally:
            app.delete()

        self.stdout.write(self.style.SUCCESS(f"\nFixtures written to {output_dir}/"))
        self.stdout.write("Commit these files if they changed.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_temp_app(manifest: dict) -> App:
    """Create an app with exactly the permissions declared in the manifest."""
    from ....app.management.commands.utils import clean_permissions

    app = App.objects.create(name="fixture-generator-temp", is_active=True)
    manifest_perms = manifest.get("permissions", [])
    if manifest_perms:
        permissions = clean_permissions(manifest_perms)
        app.permissions.set(permissions)
    return app


def _make_product_variant_with_code(code: str):
    from ....attribute import AttributeType
    from ....attribute.models import Attribute, AttributeValue
    from ....attribute.utils import associate_attribute_values_to_instance
    from ....product.models import Product, ProductType, ProductVariant

    attr, _ = Attribute.objects.get_or_create(
        slug="product-code",
        defaults={"name": "Product Code", "type": AttributeType.PRODUCT_TYPE},
    )
    attr_value, _ = AttributeValue.objects.get_or_create(
        attribute=attr,
        slug=code.lower(),
        defaults={"name": code},
    )
    product_type, _ = ProductType.objects.get_or_create(
        slug="fixture-product-type",
        defaults={"name": "Fixture Product Type", "has_variants": True},
    )
    product_type.product_attributes.add(attr)
    product = Product.objects.create(
        name="Fixture Widget",
        slug="fixture-widget",
        product_type=product_type,
    )
    associate_attribute_values_to_instance(product, {attr.pk: [attr_value]})
    return ProductVariant.objects.create(product=product, sku="FIXTURE-001")


def _make_order(channel: Channel) -> Order:
    from ....account.models import Address, User

    address = Address.objects.create(
        first_name="Fixture",
        last_name="User",
        company_name="Fixture Ltd",
        street_address_1="1 Test Street",
        city="London",
        postal_code="EC1A 1BB",
        country="GB",
    )
    user = User.objects.create_user(
        email="fixture@example.com",
        private_metadata={"xeroContactId": "00000000-0000-0000-0000-000000000000"},
    )
    return Order.objects.create(
        channel=channel,
        billing_address=address,
        user=user,
        user_email="fixture@example.com",
        currency=channel.currency_code,
        origin=OrderOrigin.DRAFT,
        status=OrderStatus.UNCONFIRMED,
        total_gross_amount=Decimal("300.00"),
        total_net_amount=Decimal("250.00"),
        undiscounted_total_gross_amount=Decimal("300.00"),
        undiscounted_total_net_amount=Decimal("250.00"),
        lines_count=1,
        deposit_required=True,
        deposit_percentage=Decimal("30.00"),
        xero_bank_account_code="090",
        shipping_xero_tax_code="RRINPUT",
    )


def _load_manifest(source: str) -> dict:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as resp:
            return json.loads(resp.read())
    path = Path(source)
    if not path.exists():
        raise CommandError(f"Manifest not found: {path}")
    return json.loads(path.read_text())


def _write(output_dir: Path, filename: str, payload, stdout) -> None:
    if payload is None:
        stdout.write(f"  ✗ {filename} — subscription returned None (schema error?)")
        return
    (output_dir / filename).write_text(json.dumps(payload, indent=2, default=str))
    stdout.write(f"  ✓ {filename}")
