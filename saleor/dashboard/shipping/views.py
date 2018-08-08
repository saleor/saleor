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
def shipping_zone_list(request):
    zones = ShippingZone.objects.prefetch_related(
        'shipping_rates').order_by('name')
    shipping_zone_filter = ShippingZoneFilter(
        request.GET, queryset=zones)
    zones = get_paginator_items(
        shipping_zone_filter.qs.distinct(), settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'shipping_zones': zones, 'filter_set': shipping_zone_filter,
        'is_empty': not shipping_zone_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/shipping/list.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_zone_add(request):
    zone = ShippingZone()
    form = ShippingZoneForm(request.POST or None, instance=zone)
    if form.is_valid():
        zone = form.save()
        msg = pgettext_lazy('Dashboard message', 'Added shipping zone')
        messages.success(request, msg)
        return redirect('dashboard:shipping-zone-details', pk=zone.pk)
    ctx = {'form': form, 'shipping_zone': form.instance}
    return TemplateResponse(request, 'dashboard/shipping/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_zone_edit(request, pk):
    zone = get_object_or_404(ShippingZone, pk=pk)
    form = ShippingZoneForm(request.POST or None, instance=zone)
    if form.is_valid():
        zone = form.save()
        msg = pgettext_lazy('Dashboard message', 'Updated shipping zone')
        messages.success(request, msg)
        return redirect('dashboard:shipping-zone-details', pk=zone.pk)
    ctx = {'form': form, 'shipping_zone': zone}
    return TemplateResponse(request, 'dashboard/shipping/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_zone_details(request, pk):
    zone = get_object_or_404(ShippingZone, pk=pk)
    shipping_rates = zone.shipping_rates.all()
    ctx = {'shipping_zone': zone, 'shipping_rates': shipping_rates}
    return TemplateResponse(
        request, 'dashboard/shipping/detail.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_zone_delete(request, pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=pk)
    if request.method == 'POST':
        shipping_zone.delete()
        msg = pgettext_lazy(
            'Dashboard message',
            '%(shipping_zone_name)s successfully removed') % {
                'shipping_zone_name': shipping_zone}
        messages.success(request, msg)
        return redirect('dashboard:shipping-zones')
    ctx = {'shipping_zone': shipping_zone}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/confirm_delete.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_rate_add(request, shipping_zone_pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=shipping_zone_pk)
    shipping_rate = ShippingRate(shipping_zone_id=shipping_zone_pk)
    form = ShippingRateForm(request.POST or None, instance=shipping_rate)
    if form.is_valid():
        shipping_rate = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added shipping price for %s'
        ) % (shipping_rate,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-zone-details', pk=shipping_zone_pk)
    ctx = {
        'form': form, 'shipping_zone': shipping_zone,
        'shipping_rate': shipping_rate}
    return TemplateResponse(
        request, 'dashboard/shipping/rate/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_rate_edit(request, shipping_zone_pk, shipping_rate_pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=shipping_zone_pk)
    shipping_rate = get_object_or_404(ShippingRate, pk=shipping_rate_pk)

    form = ShippingRateForm(request.POST or None, instance=shipping_rate)
    if form.is_valid():
        country = form.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Updated country shipping price %s') % (country,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-zone-details', pk=shipping_zone_pk)
    ctx = {
        'form': form, 'shipping_zone': shipping_zone,
        'shipping_rate': shipping_rate}
    return TemplateResponse(
        request, 'dashboard/shipping/rate/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_rate_delete(
        request, shipping_zone_pk, shipping_rate_pk=None):
    shipping_rate = get_object_or_404(ShippingRate, pk=shipping_rate_pk)
    if request.method == 'POST':
        shipping_rate.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed shipping zone %s') % (
                shipping_rate,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-zone-details', pk=shipping_zone_pk)
    ctx = {
        'shipping_rate': shipping_rate,
        'shipping_zone_pk': shipping_zone_pk}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/rate_confirm_delete.html', ctx)
