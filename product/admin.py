from django.forms import ModelForm
from django.contrib import admin
from .models import Product, Category
from mptt.admin import MPTTModelAdmin
from saleor.utils import CategoryChoiceField


class ProductForm(ModelForm):
    class Meta:
        model = Product
    category = CategoryChoiceField(Category.objects.all())


class ProductAdmin(admin.ModelAdmin):
    form = ProductForm

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, MPTTModelAdmin)
