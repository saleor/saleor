from django.utils.translation import pgettext_lazy


class ProductBulkAction:
    """Represents types of product bulk actions handled in dashboard."""

    PUBLISH = 'Publish'
    UNPUBLISH = 'Unpublish'

    CHOICES = [
        (PUBLISH, pgettext_lazy('product bulk action', 'Publish')),
        (UNPUBLISH, pgettext_lazy('product bulk action', 'Unpublish'))]
