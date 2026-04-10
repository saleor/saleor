from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ....shipping.models import ShippingMethod
from ....tax.models import TaxClass
from ...lock_objects import checkout_qs_select_for_update
from ...models import Checkout, CheckoutDelivery

# Takes around 1.1 sec for DB with 1mln+ of Checkouts, where
# less than 20% of records need to be processed
BATCH_SIZE = 1000


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def propagate_checkout_deliveries_task():
    checkout_ids = Checkout.objects.filter(
        Q(shipping_method__isnull=False) | Q(external_shipping_method_id__isnull=False),
        assigned_delivery__isnull=True,
    ).values_list("token", flat=True)[:BATCH_SIZE]

    if not checkout_ids:
        return

    with transaction.atomic():
        locked_checkout_qs = checkout_qs_select_for_update()
        locked_checkout_qs = locked_checkout_qs.filter(
            Q(shipping_method__isnull=False)
            | Q(external_shipping_method_id__isnull=False),
            token__in=checkout_ids,
            assigned_delivery__isnull=True,
        )
        locked_checkout_ids = [checkout.token for checkout in locked_checkout_qs]
        shipping_method_details = ShippingMethod.objects.only(
            "tax_class_id", "private_metadata", "metadata", "name"
        ).in_bulk(
            [
                checkout.shipping_method_id
                for checkout in locked_checkout_qs
                if checkout.shipping_method_id
            ]
        )
        tax_class_details = TaxClass.objects.only(
            "private_metadata", "metadata", "name"
        ).in_bulk([method.tax_class_id for method in shipping_method_details.values()])

        deliveries_to_create = []
        for checkout in locked_checkout_qs:
            tax_data = {}
            metadata = {}
            private_metadata = {}
            shipping_name = checkout.shipping_method_name
            if (
                checkout.shipping_method_id
                and checkout.shipping_method_id in shipping_method_details
            ):
                shipping_method = shipping_method_details[checkout.shipping_method_id]
                shipping_name = shipping_method.name
                metadata = shipping_method.metadata
                private_metadata = shipping_method.private_metadata

                tax_class_id = shipping_method.tax_class_id
                if tax_class_id and tax_class_id in tax_class_details:
                    tax_details = tax_class_details[tax_class_id]
                    tax_data["tax_class_id"] = tax_class_id
                    tax_data["tax_class_name"] = tax_details.name
                    tax_data["tax_class_private_metadata"] = (
                        tax_details.private_metadata
                    )
                    tax_data["tax_class_metadata"] = tax_details.metadata

            shipping_details = {
                "external_shipping_method_id": checkout.external_shipping_method_id,
                "built_in_shipping_method_id": checkout.shipping_method_id,
                "checkout": checkout,
                "name": shipping_name or "",
                "price_amount": checkout.undiscounted_base_shipping_price_amount,
                "currency": checkout.currency,
                "metadata": metadata,
                "private_metadata": private_metadata,
                "is_external": bool(checkout.external_shipping_method_id),
                "active": True,
                **tax_data,
            }

            delivery = CheckoutDelivery(**shipping_details)
            deliveries_to_create.append(delivery)
            checkout.assigned_delivery = delivery
            checkout.delivery_methods_stale_at = timezone.now()

        # Drop existing deliveries, as we need to be sure, that we will not hit in
        # DB constrains
        CheckoutDelivery.objects.filter(checkout_id__in=locked_checkout_ids).delete()
        CheckoutDelivery.objects.bulk_create(deliveries_to_create)
        Checkout.objects.bulk_update(
            locked_checkout_qs,
            ["assigned_delivery", "delivery_methods_stale_at"],
        )
    propagate_checkout_deliveries_task.delay()
