from django.contrib import admin
from . import models
from mptt.admin import MPTTModelAdmin

admin.site.register(models.DigitalShip)
admin.site.register(models.Ship)
admin.site.register(models.Category, MPTTModelAdmin)
admin.site.register(models.FixedProductDiscount)
