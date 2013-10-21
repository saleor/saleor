from django import forms
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.forms.models import model_to_dict, BaseInlineFormSet

from .models import Order, OrderedItem
from ..payment.models import Payment


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
            model_dict = model_to_dict(delivery.address, exclude='id')
            address = ', '.join(model_dict.values())
            self.verbose_name_plural = (
                'ShippedDelivery (%s%s): %s' % (delivery.price.gross,
                                                delivery.price.currency,
                                                address))
        if hasattr(delivery, 'email'):
            self.verbose_name_plural = (
                'Digital delivery (%s%s): %s' % (delivery.price.gross,
                                                 delivery.price.currency,
                                                 delivery.email))
        super(DeliveryInlineAdmin, self).__init__(delivery_class, admin_site)

    def get_formset(self, request, obj=None, **kwargs):
        obj = obj if not self.delivery else self.delivery
        formset = super(DeliveryInlineAdmin, self).get_formset(request, obj,
                                                               **kwargs)
        formset.instance_obj = obj
        return formset


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
    list_display = ['__unicode__', 'status', 'created', 'user']

    def total(self, obj):
        return obj.get_total().gross
    total.short_description = 'Total'

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(Order, OrderAdmin)
