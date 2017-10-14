from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...shipping.models import ShippingMethod
from ..views import superuser_required
from ...settings import DASHBOARD_PAGINATE_BY
from .forms import ShippingMethodForm, ShippingMethodCountryFormSet


@superuser_required
def shipping_method_list(request):
    methods = (ShippingMethod.objects.prefetch_related('price_per_country')
               .order_by('name'))
    methods = get_paginator_items(
        methods, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {'shipping_methods': methods}
    return TemplateResponse(request, 'dashboard/shipping/list.html', ctx)


@superuser_required
def shipping_method_edit(request, method):
    form = ShippingMethodForm(request.POST or None, instance=method)
    formset = ShippingMethodCountryFormSet(request.POST or None, instance=method)
    if form.is_valid() and formset.is_valid():
        shipping_method = form.save()
        formset.save()
        msg = pgettext_lazy(
            'Dashboard message', '%(shipping_method_name)s method saved') % {
                'shipping_method_name': shipping_method}
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-detail', pk=shipping_method.pk)
    ctx = {'shipping_method_form': form,
           'price_per_country_formset': formset, 'shipping_method': method}
    return TemplateResponse(request, 'dashboard/shipping/form.html', ctx)


@superuser_required
def shipping_method_add(request):
    method = ShippingMethod()
    return shipping_method_edit(request, method)


@superuser_required
def shipping_method_update(request, pk):
    method = get_object_or_404(ShippingMethod, pk=pk)
    return shipping_method_edit(request, method)


@superuser_required
def shipping_method_detail(request, pk):
    shipping_methods = ShippingMethod.objects.prefetch_related(
        'price_per_country').all()
    method = get_object_or_404(shipping_methods, pk=pk)
    method_countries = method.price_per_country.all()
    ctx = {'shipping_method': method, 'method_countries': method_countries}
    return TemplateResponse(
        request, 'dashboard/shipping/detail.html', ctx)


@superuser_required
def shipping_method_delete(request, pk):
    shipping_method = get_object_or_404(ShippingMethod, pk=pk)
    if request.method == 'POST':
        shipping_method.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message', '%(shipping_method_name)s successfully deleted') % {
                    'shipping_method_name': shipping_method})
        return redirect('dashboard:shipping-methods')
    ctx = {'shipping_method': shipping_method}
    return TemplateResponse(request, 'dashboard/shipping/modal/confirm_delete.html', ctx)
