from django.db.models import Exists, OuterRef

from ....account.models import Address
from ....celeryconf import app
from ....checkout.models import Checkout
from ....core.db.connection import allow_writer
from ....order import OrderOrigin
from ....order.models import Order

# Takes about 0.5 second to process
BATCH_SIZE = 250


@app.task
@allow_writer()
def fix_shared_address_instances_task():
    """Fix shared address instances between checkouts and orders."""
    orders = Order.objects.filter(origin=OrderOrigin.CHECKOUT)

    # first process billing addresses
    field = "billing_address"
    checkouts = Checkout.objects.filter(
        Exists(orders.filter(billing_address_id=OuterRef("billing_address_id"))),
        billing_address_id__isnull=False,
    )[:BATCH_SIZE]

    if not checkouts:
        # then process shipping addresses if all billing addresses are done
        checkouts = Checkout.objects.filter(
            Exists(orders.filter(shipping_address_id=OuterRef("shipping_address_id"))),
            shipping_address_id__isnull=False,
        )[:BATCH_SIZE]
        field = "shipping_address"

    if not checkouts:
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

    fix_shared_address_instances_task.delay()
