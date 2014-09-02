from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.forms.models import BaseInlineFormSet
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .models import Order, OrderedItem, Payment


def format_address(address):
    address = render_to_string('userprofile/snippets/address-details.html',
                               {'address': address})
    # avoid django's linebreaks breaking the result
    return address.replace('\n', '')


class OrderModelAdmin(ModelAdmin):

    def get_inline_instances(self, request, order=None):
        inlines = super(OrderModelAdmin, self).get_inline_instances(request,
                                                                    order)
        if order:
            inlines.extend([
                DeliveryInlineAdmin(self.model, self.admin_site, group)
                for group in order])
        return inlines


class PaymentInlineAdmin(admin.TabularInline):

    model = Payment
    extra = 0
    readonly_fields = ['variant', 'status', 'transaction_id', 'currency',
                       'total', 'delivery', 'description', 'tax',
                       'billing_first_name', 'billing_last_name',
                       'billing_address_1', 'billing_address_2',
                       'billing_city', 'billing_country_code',
                       'billing_country_area', 'billing_postcode']
    exclude = ['token', 'extra_data']
    can_delete = False


class DeliveryFormSet(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        kwargs['instance'] = self.instance_obj
        super(DeliveryFormSet, self).__init__(*args, **kwargs)


class DeliveryInlineAdmin(admin.TabularInline):

    model = OrderedItem
    formset = DeliveryFormSet

    def __init__(self, parent_model, admin_site, delivery):
        self.delivery = delivery
        delivery_class = delivery.__class__
        if hasattr(delivery, 'address'):
            address = format_address(delivery.address)
            self.verbose_name_plural = (
                mark_safe(
                    '%s: %s %s<br>%s' % (
                        delivery,
                        delivery.price.gross,
                        delivery.price.currency,
                        address)))
        if hasattr(delivery, 'email'):
            self.verbose_name_plural = (
                mark_safe(
                    '%s: %s %s<br>%s' % (
                        delivery,
                        delivery.price.gross,
                        delivery.price.currency,
                        delivery.email)))
        super(DeliveryInlineAdmin, self).__init__(delivery_class, admin_site)

    def get_formset(self, request, obj=None, **kwargs):
        obj = obj if not self.delivery else self.delivery
        formset = super(DeliveryInlineAdmin, self).get_formset(request, obj,
                                                               **kwargs)
        formset.instance_obj = obj
        return formset


class OrderAdmin(OrderModelAdmin):

    inlines = [PaymentInlineAdmin]
    exclude = ['token']
    readonly_fields = ['customer', 'total']
    list_display = ['__str__', 'status', 'created', 'user']

    def customer(self, obj):
        return format_address(obj.billing_address)
    customer.allow_tags = True

    def total(self, obj):
        total = obj.get_total()
        return '%s %s' % (total.gross, total.currency)
    total.short_description = 'Total'

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(Order, OrderAdmin)
