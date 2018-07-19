from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...shipping.models import ShippingMethod, ShippingMethodCountry
from ..views import staff_member_required
from .filters import ShippingMethodFilter
from .forms import ShippingMethodCountryForm, ShippingMethodForm


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_list(request):
    methods = ShippingMethod.objects.prefetch_related(
        'price_per_country').order_by('name')
    shipping_method_filter = ShippingMethodFilter(
        request.GET, queryset=methods)
    methods = get_paginator_items(
        shipping_method_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'shipping_methods': methods, 'filter_set': shipping_method_filter,
        'is_empty': not shipping_method_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/shipping/list.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_add(request):
    method = ShippingMethod()
    form = ShippingMethodForm(request.POST or None, instance=method)
    if form.is_valid():
        method = form.save()
        msg = pgettext_lazy('Dashboard message', 'Added shipping method')
        messages.success(request, msg)
        return redirect('dashboard:shipping-method-details', pk=method.pk)
    ctx = {'form': form, 'shipping_method': form.instance}
    return TemplateResponse(request, 'dashboard/shipping/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_edit(request, pk):
    method = get_object_or_404(ShippingMethod, pk=pk)
    form = ShippingMethodForm(request.POST or None, instance=method)
    if form.is_valid():
        method = form.save()
        msg = pgettext_lazy('Dashboard message', 'Updated shipping method')
        messages.success(request, msg)
        return redirect('dashboard:shipping-method-details', pk=method.pk)
    ctx = {'form': form, 'shipping_method': method}
    return TemplateResponse(request, 'dashboard/shipping/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_details(request, pk):
    shipping_methods = ShippingMethod.objects.prefetch_related(
        'price_per_country').all()
    method = get_object_or_404(shipping_methods, pk=pk)
    method_countries = method.price_per_country.all()
    ctx = {'shipping_method': method, 'method_countries': method_countries}
    return TemplateResponse(
        request, 'dashboard/shipping/detail.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_delete(request, pk):
    shipping_method = get_object_or_404(ShippingMethod, pk=pk)
    if request.method == 'POST':
        shipping_method.delete()
        msg = pgettext_lazy(
            'Dashboard message',
            '%(shipping_method_name)s successfully removed') % {
                'shipping_method_name': shipping_method}
        messages.success(request, msg)
        return redirect('dashboard:shipping-methods')
    ctx = {'shipping_method': shipping_method}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/confirm_delete.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_country_add(request, shipping_method_pk):
    shipping_method = get_object_or_404(ShippingMethod, pk=shipping_method_pk)
    country = ShippingMethodCountry(shipping_method_id=shipping_method_pk)
    form = ShippingMethodCountryForm(request.POST or None, instance=country)
    if form.is_valid():
        country = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added shipping price for %s') % (country,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-details', pk=shipping_method_pk)
    ctx = {
        'form': form, 'shipping_method': shipping_method, 'country': country}
    return TemplateResponse(
        request, 'dashboard/shipping/country/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_country_edit(request, shipping_method_pk, country_pk):
    shipping_method = get_object_or_404(ShippingMethod, pk=shipping_method_pk)
    country = get_object_or_404(ShippingMethodCountry, pk=country_pk)
    form = ShippingMethodCountryForm(request.POST or None, instance=country)
    if form.is_valid():
        country = form.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Updated country shipping price %s') % (country,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-details', pk=shipping_method_pk)
    ctx = {
        'form': form, 'shipping_method': shipping_method, 'country': country}
    return TemplateResponse(
        request, 'dashboard/shipping/country/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_country_delete(
        request, shipping_method_pk, country_pk=None):
    country = get_object_or_404(ShippingMethodCountry, pk=country_pk)
    if request.method == 'POST':
        country.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed shipping method %s') % (country,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-details', pk=shipping_method_pk)
    ctx = {'country': country, 'shipping_method_pk': shipping_method_pk}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/country_confirm_delete.html', ctx)
