from __future__ import unicode_literals

from django import forms
from django.db.models import Q
from django.utils.translation import pgettext_lazy

from ...order import OrderStatus


class CustomerSearchForm(forms.Form):
    email = forms.CharField(
        required=False,
        label=pgettext_lazy(
            'Customer search form field label',
            'Email'))
    name = forms.CharField(
        required=False,
        label=pgettext_lazy(
            'Customer search form field label',
            'Name'))
    order_status = forms.BooleanField(
        required=False, initial=True,
        label=pgettext_lazy(
            'Customer search form label for field `order_status`',
            'With open orders'))

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super(CustomerSearchForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        for field in ['email', 'name']:
            data[field] = data[field].strip()
        return data

    def search(self):
        queryset = self.queryset
        data = self.cleaned_data
        if data['email']:
            queryset = queryset.filter(email__icontains=data['email'])
        if data['name']:
            parts = data['name'].split()
            if len(parts) == 2:
                query = ((Q(addresses__first_name__icontains=parts[0]) |
                          Q(addresses__last_name__icontains=parts[1])) |
                         (Q(addresses__first_name__icontains=parts[1]) |
                          Q(addresses__last_name__icontains=parts[0])))
            else:
                query = (Q(addresses__first_name__icontains=data['name']) |
                         Q(addresses__last_name__icontains=data['name']))
            queryset = queryset.filter(query).distinct()
        if data['order_status']:
            open_order = [
                OrderStatus.NEW, OrderStatus.PAYMENT_PENDING,
                OrderStatus.FULLY_PAID]
            queryset = queryset.filter(orders__status__in=open_order)

        return queryset
