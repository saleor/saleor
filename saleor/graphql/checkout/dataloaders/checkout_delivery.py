from collections import defaultdict
from uuid import UUID

from ....checkout.models import CheckoutDelivery
from ...core.dataloaders import DataLoader


class CheckoutDeliveryByIdLoader(DataLoader[UUID, CheckoutDelivery]):
    context_key = "checkout_delivery_by_id"

    def batch_load(self, keys):
        shipping_methods = CheckoutDelivery.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [shipping_methods.get(key) for key in keys]


class CheckoutDeliveriesOnlyValidByCheckoutIdLoader(
    DataLoader[UUID, list[CheckoutDelivery]]
):
    context_key = "checkout_deliveries_by_checkout_id"

    def batch_load(self, keys):
        shipping_methods = CheckoutDelivery.objects.using(
            self.database_connection_name
        ).filter(checkout_id__in=keys, is_valid=True)
        shipping_methods_map: dict[UUID, list[CheckoutDelivery]] = defaultdict(list)
        for shipping_method in shipping_methods:
            shipping_methods_map[shipping_method.checkout_id].append(shipping_method)
        return [shipping_methods_map[key] for key in keys]
