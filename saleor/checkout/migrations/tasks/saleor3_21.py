from django.db.models import Exists, OuterRef

from ....account.models import Address
from ....celeryconf import app
from ....checkout.models import Checkout
from ....core.db.connection import allow_writer
from ....order.models import Order

# Takes about 0.5 second to process
BATCH_SIZE = 250


BILLING_FIELD = "billing_address"
SHIPPING_FIELD = "shipping_address"


@app.task
@allow_writer()
def fix_shared_address_instances_task(field=BILLING_FIELD):
    """Fix shared address instances between checkouts and orders.

    First process billing addresses, then shipping addresses.
    """
    filter = {
        f"{field}_id__isnull": False,
    }
    checkouts = Checkout.objects.filter(
        Exists(Order.objects.filter(**{f"{field}_id": OuterRef(f"{field}_id")})),
        **filter,
    )[:BATCH_SIZE]

    if not checkouts:
        if field == BILLING_FIELD:
            fix_shared_address_instances_task.delay(field=SHIPPING_FIELD)
        return

    checkout_instances = []
    addresses_to_create = []
    for checkout in checkouts:
        address_data = getattr(checkout, field).as_data()
        addresses_to_create.append(Address(**address_data))
        checkout_instances.append(checkout)
    # address instances returned in the same order as in the provided list
    addresses = Address.objects.bulk_create(addresses_to_create)

    for checkout, address in zip(checkout_instances, addresses, strict=True):
        setattr(checkout, field, address)
    Checkout.objects.bulk_update(checkout_instances, [field])

    fix_shared_address_instances_task.delay(field=field)
