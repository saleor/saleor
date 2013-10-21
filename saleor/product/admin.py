from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from . import models


class ImageAdminInline(admin.StackedInline):

    model = models.ProductImage


class ProductAdmin(admin.ModelAdmin):

    inlines = [ImageAdminInline]


admin.site.register(models.DigitalShip, ProductAdmin)
admin.site.register(models.Ship, ProductAdmin)
admin.site.register(models.Category, MPTTModelAdmin)
admin.site.register(models.FixedProductDiscount)
