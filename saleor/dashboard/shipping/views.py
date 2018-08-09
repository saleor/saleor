from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...shipping.models import ShippingMethod, ShippingZone
from ..views import staff_member_required
from .filters import ShippingZoneFilter
from .forms import ShippingMethodForm, ShippingZoneForm


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_zone_list(request):
    zones = ShippingZone.objects.prefetch_related(
        'shipping_methods').order_by('name')
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
    price_based = zone.shipping_methods.price_based()
    weight_based = zone.shipping_methods.weight_based()
    ctx = {
        'shipping_zone': zone, 'price_based': price_based,
        'weight_based': weight_based}
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
def shipping_method_add(request, shipping_zone_pk, type):
    shipping_zone = get_object_or_404(ShippingZone, pk=shipping_zone_pk)
    shipping_method = ShippingMethod(
        shipping_zone_id=shipping_zone_pk, type=type)
    form = ShippingMethodForm(request.POST or None, instance=shipping_method)
    if form.is_valid():
        shipping_method = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added shipping price for %s'
        ) % (shipping_method,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-zone-details', pk=shipping_zone_pk)
    ctx = {
        'form': form, 'shipping_zone': shipping_zone,
        'shipping_method': shipping_method}
    return TemplateResponse(
        request, 'dashboard/shipping/methods/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_edit(request, shipping_zone_pk, shipping_method_pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=shipping_zone_pk)
    shipping_method = get_object_or_404(ShippingMethod, pk=shipping_method_pk)

    form = ShippingMethodForm(
        request.POST or None, instance=shipping_method)
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
        'shipping_method': shipping_method}
    return TemplateResponse(
        request, 'dashboard/shipping/methods/form.html', ctx)


@staff_member_required
@permission_required('shipping.manage_shipping')
def shipping_method_delete(
        request, shipping_zone_pk, shipping_method_pk=None):
    shipping_method = get_object_or_404(ShippingMethod, pk=shipping_method_pk)
    if request.method == 'POST':
        shipping_method.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed shipping zone %s') % (
                shipping_method,)
        messages.success(request, msg)
        return redirect(
            'dashboard:shipping-zone-details', pk=shipping_zone_pk)
    ctx = {
        'shipping_method': shipping_method,
        'shipping_zone_pk': shipping_zone_pk}
    return TemplateResponse(
        request, 'dashboard/shipping/modal/rate_confirm_delete.html', ctx)
