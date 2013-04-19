from .models import Order, OrderedItem
from django import forms
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.forms.models import model_to_dict
from payment.models import Payment


class OrderModelAdmin(ModelAdmin):

    def get_inline_instances(self, request, order=None):
        inlines = super(OrderModelAdmin, self).get_inline_instances(request,
                                                                    order)
        if order:
            inlines.extend([
                DeliveryInlineAdmin(self.model, self.admin_site, group)
                for group in order.groups.all()])
        return inlines


class PaymentInlineAdmin(admin.TabularInline):

    model = Payment
    extra = 0
    readonly_fields = ['variant', 'status', 'transaction_id', 'currency',
                       'total', 'delivery', 'description', 'first_name', 'tax',
                       'last_name', 'city', 'country_area', 'zip', 'country']
    exclude = ['token', 'extra_data']
    can_delete = False


class DeliveryInlineAdmin(admin.TabularInline):

    model = OrderedItem

    def __init__(self, parent_model, admin_site, delivery):
        self.delivery = delivery
        delivery_class = delivery.__class__
        if hasattr(delivery, 'address'):
            model_dict = model_to_dict(delivery.address, exclude='id')
            address = ', '.join(model_dict.values())
            self.verbose_name_plural = (
                u'ShippedDelivery (%s%s): %s' % (delivery.price.gross,
                                                 delivery.price.currency,
                                                 address))
        if hasattr(delivery, 'email'):
            self.verbose_name_plural = (
                u'Digital delivery (%s%s): %s' % (delivery.price.gross,
                                                  delivery.price.currency,
                                                  delivery.email))
        super(DeliveryInlineAdmin, self).__init__(delivery_class, admin_site)

    def get_formset(self, request, obj=None, **kwargs):
        obj = obj if not self.delivery else self.delivery
        return super(DeliveryInlineAdmin, self).get_formset(request, obj,
                                                            **kwargs)


class OrderAdminForm(forms.ModelForm):

    class Meta:
        model = Order

    total = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(OrderAdminForm, self).__init__(*args, **kwargs)
        order = kwargs.get('instance')
        if order:
            self.fields['total'].initial = order.get_total().gross


class OrderAdmin(OrderModelAdmin):

    inlines = [PaymentInlineAdmin]
    exclude = ['token']
    readonly_fields = ['user', 'billing_address', 'total']
    form = OrderAdminForm

    def total(self, obj):
        return obj.get_total().gross
    total.short_description = u'Total'


admin.site.register(Order, OrderAdmin)
