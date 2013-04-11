from django.contrib import admin
from .models import Order
from payment.models import Payment


class PaymentInlineAdmin(admin.TabularInline):

    model = Payment


class OrderAdmin(admin.ModelAdmin):

    inlines = [PaymentInlineAdmin]

admin.site.register(Order, OrderAdmin)
