from django.contrib import admin
from .models import Order, OrderedItem, DeliveryGroup
from payment.models import Payment


class PaymentInlineAdmin(admin.TabularInline):

    model = Payment
    extra = 0
    readonly_fields = ['variant', 'status', 'transaction_id', 'currency',
                       'total', 'delivery', 'description', 'first_name', 'tax',
                       'last_name', 'city', 'country_area', 'zip', 'country']
    exclude = ['token', 'extra_data', 'success_url', 'cancel_url']


class DeliveryInlineAdmin(admin.TabularInline):

    model = DeliveryGroup


class OrderAdmin(admin.ModelAdmin):

    inlines = [PaymentInlineAdmin, DeliveryInlineAdmin]
    exclude = ['token']
    readonly_fields = ['user', 'billing_address']

admin.site.register(Order, OrderAdmin)
