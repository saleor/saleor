from django.utils.translation import pgettext_lazy


class ProductAvailabilityStatus:
    NOT_PUBLISHED = 'not-published'
    VARIANTS_MISSSING = 'variants-missing'
    OUT_OF_STOCK = 'out-of-stock'
    LOW_STOCK = 'low-stock'
    NOT_YET_AVAILABLE = 'not-yet-available'
    READY_FOR_PURCHASE = 'ready-for-purchase'

    @staticmethod
    def get_display(status):
        if status == ProductAvailabilityStatus.NOT_PUBLISHED:
            return pgettext_lazy('Product status', 'not published')
        elif status == ProductAvailabilityStatus.VARIANTS_MISSSING:
            return pgettext_lazy('Product status', 'variants missing')
        elif status == ProductAvailabilityStatus.OUT_OF_STOCK:
            return pgettext_lazy('Product status', 'out of stock')
        elif status == ProductAvailabilityStatus.LOW_STOCK:
            return pgettext_lazy('Product status', 'stock running low')
        elif status == ProductAvailabilityStatus.NOT_YET_AVAILABLE:
            return pgettext_lazy('Product status', 'not yet available')
        elif status == ProductAvailabilityStatus.READY_FOR_PURCHASE:
            return pgettext_lazy('Product status', 'ready for purchase')
        else:
            raise NotImplementedError('Unknown status: %s' % status)


class VariantAvailabilityStatus:
    AVAILABLE = 'available'
    OUT_OF_STOCK = 'out-of-stock'

    @staticmethod
    def get_display(status):
        if status == VariantAvailabilityStatus.AVAILABLE:
            return pgettext_lazy('Variant status', 'available')
        elif status == VariantAvailabilityStatus.OUT_OF_STOCK:
            return pgettext_lazy('Variant status', 'out of stock')
        else:
            raise NotImplementedError('Unknown status: %s' % status)
