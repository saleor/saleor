from django.contrib import admin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from . import filters
from .. import models


@admin.register(models.RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created', 'revoked', 'is_expired']
    list_filter = (filters.RevokedFilter, filters.ExpiredFilter)
    raw_id_fields = ('user',)
    search_fields = ('token',)
    actions = ('revoke',)

    def revoke(self, request, queryset):
        queryset.update(revoked=timezone.now())

    revoke.short_description = _('Revoke selected %(verbose_name_plural)s')

    def is_expired(self, obj):
        return obj.is_expired()

    is_expired.boolean = True
    is_expired.short_description = _('is expired')
