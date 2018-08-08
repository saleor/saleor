from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...shipping.models import ShippingRate, ShippingZone
from ..views import staff_member_required
from .filters import ShippingZoneFilter
from .forms import ShippingRateForm, ShippingZoneForm


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_list(request):
    zones = ShippingZone.objects.prefetch_related(
        'shipping_methods').order_by('name')
    shipping_method_filter = ShippingZoneFilter(
        request.GET, queryset=zones)
    zones = get_paginator_items(
        shipping_method_filter.qs.distinct(), settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'shipping_zones': zones, 'filter_set': shipping_method_filter,
        'is_empty': not shipping_method_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/shipping/list.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_add(request):
    zone = ShippingZone()
    form = ShippingZoneForm(request.POST or None, instance=zone)
    if form.is_valid():
        zone = form.save()
        msg = pgettext_lazy('Dashboard message', 'Added shipping zone')
        messages.success(request, msg)
        return redirect('dashboard:shipping-method-details', pk=zone.pk)
    ctx = {'form': form, 'shipping_method': form.instance}
    return TemplateResponse(request, 'dashboard/shipping/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_edit(request, pk):
    zone = get_object_or_404(ShippingZone, pk=pk)
    form = ShippingZoneForm(request.POST or None, instance=zone)
    if form.is_valid():
        zone = form.save()
        msg = pgettext_lazy('Dashboard message', 'Updated shipping zone')
        messages.success(request, msg)
        return redirect('dashboard:shipping-method-details', pk=zone.pk)
    ctx = {'form': form, 'shipping_method': zone}
    return TemplateResponse(request, 'dashboard/shipping/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_details(request, pk):
    zone = get_object_or_404(ShippingZone, pk=pk)
    shipping_rates = zone.shipping_methods.all()
    ctx = {'shipping_method': zone, 'shipping_rates': shipping_rates}
    return TemplateResponse(
        request, 'dashboard/shipping/detail.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_delete(request, pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=pk)
    if request.method == 'POST':
        shipping_zone.delete()
        msg = pgettext_lazy(
            'Dashboard message',
            '%(shipping_zone_name)s successfully removed') % {
                'shipping_zone_name': shipping_zone}
        messages.success(request, msg)
        return redirect('dashboard:shipping-methods')
    ctx = {'shipping_zone': shipping_zone}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/confirm_delete.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_rate_add(request, shipping_method_pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=shipping_method_pk)
    shipping_rate = ShippingRate(shipping_zone_id=shipping_method_pk)
    form = ShippingRateForm(request.POST or None, instance=shipping_rate)
    if form.is_valid():
        shipping_rate = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added shipping price for %s'
        ) % (shipping_rate,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-details', pk=shipping_method_pk)
    ctx = {
        'form': form, 'shipping_method': shipping_zone,
        'shipping_rate': shipping_rate}
    return TemplateResponse(
        request, 'dashboard/shipping/rate/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_rate_edit(request, shipping_method_pk, rate_pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=shipping_method_pk)
    shipping_rate = get_object_or_404(ShippingRate, pk=rate_pk)

    form = ShippingRateForm(request.POST or None, instance=shipping_rate)
    if form.is_valid():
        country = form.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Updated country shipping price %s') % (country,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-details', pk=shipping_method_pk)
    ctx = {
        'form': form, 'shipping_method': shipping_zone,
        'shipping_rate': shipping_rate}
    return TemplateResponse(
        request, 'dashboard/shipping/rate/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_rate_delete(
        request, shipping_method_pk, rate_pk=None):
    shipping_rate = get_object_or_404(ShippingRate, pk=rate_pk)
    if request.method == 'POST':
        shipping_rate.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed shipping method %s') % (
                shipping_rate,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-method-details', pk=shipping_method_pk)
    ctx = {
        'shipping_rate': shipping_rate,
        'shipping_method_pk': shipping_method_pk}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/rate_confirm_delete.html', ctx)
