from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...core.utils import get_paginator_items

from ...shipping.models import ShippingMethod
from .forms import ShippingMethodForm, ShippingMethodCountryFormSet


@staff_member_required
def shipping_method_list(request):
    methods = ShippingMethod.objects.prefetch_related('price_per_country').all()
    methods = get_paginator_items(methods, 30, request.GET.get('page'))
    ctx = {'shipping_methods': methods}
    return TemplateResponse(request, 'dashboard/shipping/method_list.html', ctx)


def shipping_method_edit(request, method):
    form = ShippingMethodForm(request.POST or None, instance=method)
    formset = ShippingMethodCountryFormSet(request.POST or None, instance=method)
    if form.is_valid() and formset.is_valid():
        method = form.save()
        formset.save()
        msg = _('%s method saved') % method
        messages.success(request, msg)
        return redirect('dashboard:shipping-methods')
    ctx = {'shipping_method_form': form,
           'price_per_country_formset': formset, 'shipping_method': method}
    return TemplateResponse(request, 'dashboard/shipping/method_form.html', ctx)


@staff_member_required
def shipping_method_add(request):
    method = ShippingMethod()
    return shipping_method_edit(request, method)


@staff_member_required
def shipping_method_detail(request, pk):
    method = get_object_or_404(ShippingMethod, pk=pk)
    return shipping_method_edit(request, method)


@staff_member_required
def shipping_method_delete(request, pk):
    shipping_method = get_object_or_404(ShippingMethod, pk=pk)
    if request.method == 'POST':
        shipping_method.delete()
        messages.success(
            request, _('%(shipping_method_name)s successfully deleted') % {
                'shipping_method_name': shipping_method})
        return redirect('dashboard:shipping-methods')
    ctx = {'shipping_method': shipping_method}
    return TemplateResponse(request, 'dashboard/shipping/method_delete.html', ctx)
