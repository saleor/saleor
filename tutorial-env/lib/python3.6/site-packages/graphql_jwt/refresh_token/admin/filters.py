from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

__all__ = [
    'ExpiredFilter',
    'RevokedFilter',
]


class BooleanListFilter(SimpleListFilter):

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )


class ExpiredFilter(BooleanListFilter):
    title = _('Expired')
    parameter_name = 'expired'

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.expired().filter(expired=True)

        if self.value() == 'no':
            return queryset.expired().filter(expired=False)


class RevokedFilter(BooleanListFilter):
    title = _('Revoked')
    parameter_name = 'revoked'

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(revoked__isnull=False)

        if self.value() == 'no':
            return queryset.filter(revoked__isnull=True)
