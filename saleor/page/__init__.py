from django.utils.translation import pgettext_lazy


class PageStatus:
    """Enum page statuses"""
    DRAFT = 'draft'
    PUBLIC = 'public'

    CHOICES = (
        (DRAFT, pgettext_lazy('page status', 'Draft')),
        (PUBLIC, pgettext_lazy('page status', 'Public')))
