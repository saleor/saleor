from prices import PriceModifier


class Discount(PriceModifier):

    def can_apply(self, item, **kwargs):
        raise NotImplementedError()

    def apply_to_item(self, item, **kwargs):
        raise NotImplementedError()


class ItemDiscount(Discount):

    item = None

    def can_apply(self, item, **kwargs):
        return hasattr(item, 'get_price')

    def apply_to_item(self, item, **kwargs):
        self.item = item
        # We have to add set_price method to Item Class
        item.price += self


class ItemSetDiscount(Discount):

    item_set = None

    def can_apply(self, item, **kwargs):
        return hasattr(item, 'get_total')

    def apply_to_item(self, item_set, **kwargs):
        self.item = item_set
        for item in item_set:
            # We definitely have to add set_price method to Item Class
            item.product.price += self


class DiscountManager(list):

    def apply(self, item, **kwargs):
        for discount in self.filter(item, **kwargs):
            discount.apply_to_item(item)

    def filter(self, item, **kwargs):
        return [discount for discount in self
                if discount.can_apply(item, **kwargs)]


def get_discounts(request):
    if hasattr(request, 'discounts'):
        return request.discounts
    from .models import SelectedProduct
    selected_products = SelectedProduct.objects.all()
    request.discounts = DiscountManager(selected_products)
    return request.discounts
