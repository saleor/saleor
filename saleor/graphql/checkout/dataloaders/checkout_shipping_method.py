from collections import defaultdict
from uuid import UUID

from ....checkout.models import CheckoutShippingMethod
from ...core.dataloaders import DataLoader


class CheckoutShippingMethodByIdLoader(DataLoader[UUID, CheckoutShippingMethod]):
    context_key = "checkout_shipping_method_by_id"

    def batch_load(self, keys):
        shipping_methods = CheckoutShippingMethod.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [shipping_methods.get(key) for key in keys]


class CheckoutShippingMethodsOnlyValidByCheckoutIdLoader(
    DataLoader[UUID, list[CheckoutShippingMethod]]
):
    context_key = "checkout_shipping_methods_by_checkout_id"

    def batch_load(self, keys):
        shipping_methods = CheckoutShippingMethod.objects.using(
            self.database_connection_name
        ).filter(checkout_id__in=keys, is_valid=True)
        shipping_methods_map: dict[UUID, list[CheckoutShippingMethod]] = defaultdict(
            list
        )
        for shipping_method in shipping_methods:
            shipping_methods_map[shipping_method.checkout_id].append(shipping_method)
        return [shipping_methods_map[key] for key in keys]
