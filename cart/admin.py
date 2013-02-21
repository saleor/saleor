from django.contrib import admin
from .models import Cart, CartItem

class CartInlineAdmin(admin.TabularInline):

    model = CartItem

class CartAdmin(admin.ModelAdmin):

    inlines = [CartInlineAdmin]

admin.site.register(Cart, CartAdmin)
