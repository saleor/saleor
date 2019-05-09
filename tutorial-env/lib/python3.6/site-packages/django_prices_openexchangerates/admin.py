from django.contrib import admin
from .models import ConversionRate


class ConversionRateAdmin(admin.ModelAdmin):
    list_display = ('rate', 'to_currency')

admin.site.register(ConversionRate, ConversionRateAdmin)
