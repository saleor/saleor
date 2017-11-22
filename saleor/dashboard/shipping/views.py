from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items

from ..views import staff_member_required
from ...shipping.models import ShippingMethod, ShippingMethodCountry
from ...settings import DASHBOARD_PAGINATE_BY
from .forms import ShippingMethodForm, ShippingMethodCountryForm


@staff_member_required
@permission_required('shipping.view_shipping')
def shipping_method_list(request):
    methods = (ShippingMethod.objects.prefetch_related('price_per_country')
               .order_by('name'))
    methods = get_paginator_items(
        methods, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {'shipping_methods': methods}
    return TemplateResponse(request, 'dashboard/shipping/list.html', ctx)


@staff_member_required
@permission_required('shipping.edit_shipping')
def shipping_method_edit(request, pk=None):
    if pk:
        method = get_object_or_404(ShippingMethod, pk=pk)
    else:
        method = ShippingMethod()
    form = ShippingMethodForm(request.POST or None, instance=method)
    if form.is_valid():
        method = form.save()
        msg = pgettext_lazy(
            'dashboard message', 'Updated shipping method') \
            if pk else pgettext_lazy(
            'Dashboard message', 'Added shipping method')
        messages.success(request, msg)
        return redirect('dashboard:shipping-method-detail', pk=method.pk)
    ctx = {'form': form, 'shipping_method': method}
    return TemplateResponse(
        request, 'dashboard/shipping/form.html', ctx)


@staff_member_required
@permission_required('shipping.view_shipping')
def shipping_method_detail(request, pk):
    shipping_methods = ShippingMethod.objects.prefetch_related(
        'price_per_country').all()
    method = get_object_or_404(shipping_methods, pk=pk)
    method_countries = method.price_per_country.all()
    ctx = {'shipping_method': method, 'method_countries': method_countries}
    return TemplateResponse(
        request, 'dashboard/shipping/detail.html', ctx)


@staff_member_required
@permission_required('shipping.edit_shipping')
def shipping_method_delete(request, pk):
    shipping_method = get_object_or_404(ShippingMethod, pk=pk)
    if request.method == 'POST':
        shipping_method.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message',
                '%(shipping_method_name)s successfully deleted') % {
                    'shipping_method_name': shipping_method})
        return redirect('dashboard:shipping-methods')
    ctx = {'shipping_method': shipping_method}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/confirm_delete.html', ctx)


@staff_member_required
@permission_required('shipping.edit_shipping')
def shipping_method_country_edit(request, shipping_method_pk, country_pk=None):
    shipping_method = get_object_or_404(ShippingMethod, pk=shipping_method_pk)
    if country_pk:
        country = get_object_or_404(ShippingMethodCountry, pk=country_pk)
    else:
        country = ShippingMethodCountry(shipping_method_id=shipping_method_pk)
    form = ShippingMethodCountryForm(request.POST or None, instance=country)
    if form.is_valid():
        country = form.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Updated country shipping price %s') % (country,) \
            if country_pk else pgettext_lazy(
            'Dashboard message', 'Added shipping price for %s') % (country,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-detail', pk=shipping_method_pk)
    ctx = {'form': form, 'shipping_method': shipping_method,
           'country': country}
    return TemplateResponse(
        request, 'dashboard/shipping/country/form.html', ctx)


@staff_member_required
@permission_required('shipping.edit_shipping')
def shipping_method_country_delete(
        request, shipping_method_pk, country_pk=None):
    country = get_object_or_404(ShippingMethodCountry, pk=country_pk)
    if request.method == 'POST':
        country.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message',
                'Removed shipping method %s') %
            (country,))
        return redirect(
            'dashboard:shipping-method-detail', pk=shipping_method_pk)
    return TemplateResponse(
        request, 'dashboard/shipping/modal/country_confirm_delete.html',
        {'country': country, 'shipping_method_pk': shipping_method_pk})
