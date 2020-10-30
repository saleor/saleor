from ...shipping.models import ShippingMethod
from ..core.dataloaders import DataLoader


class ShippingMethodByIdLoader(DataLoader):
    context_key = "shippingmethod_by_id"

    def batch_load(self, keys):
        shipping_methods = ShippingMethod.objects.in_bulk(keys)
        return [shipping_methods.get(shipping_method_id) for shipping_method_id in keys]
