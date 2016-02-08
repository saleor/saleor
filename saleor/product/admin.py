from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from ..discount.models import Sale
from .models import (ProductImage, Category)
from .forms import ImageInline


class ImageAdminInline(admin.StackedInline):
    model = ProductImage
    formset = ImageInline


class ProductCollectionAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(Category, MPTTModelAdmin)
admin.site.register(Sale)
