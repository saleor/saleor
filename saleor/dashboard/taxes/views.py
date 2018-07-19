from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from django_countries.fields import Country
from django_prices_vatlayer.models import VAT

from ...core.i18n import VAT_RATE_TYPE_TRANSLATIONS
from ...core.utils import get_paginator_items
from ...core.utils.taxes import get_taxes_for_country
from ...dashboard.taxes.filters import TaxFilter
from ...dashboard.taxes.forms import TaxesConfigurationForm
from ...dashboard.views import staff_member_required


@staff_member_required
def tax_list(request):
    taxes = VAT.objects.order_by('country_code')
    tax_filter = TaxFilter(request.GET, queryset=taxes)
    taxes = get_paginator_items(
        tax_filter.qs, settings.DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {
        'taxes': taxes, 'filter_set': tax_filter,
        'is_empty': not tax_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/taxes/list.html', ctx)


@staff_member_required
def tax_details(request, country_code):
    tax = get_object_or_404(VAT, country_code=country_code)
    tax_rates = get_taxes_for_country(Country(country_code))
    tax_rates = [
        (VAT_RATE_TYPE_TRANSLATIONS.get(rate_name, rate_name), tax['value'])
        for rate_name, tax in tax_rates.items()]
    ctx = {'tax': tax, 'tax_rates': sorted(tax_rates)}
    return TemplateResponse(request, 'dashboard/taxes/details.html', ctx)


@staff_member_required
@permission_required('site.manage_settings')
def configure_taxes(request):
    site_settings = request.site.settings
    taxes_form = TaxesConfigurationForm(
        request.POST or None, instance=site_settings)
    if taxes_form.is_valid():
        taxes_form.save()
        msg = pgettext_lazy('Dashboard message', 'Updated taxes settings')
        messages.success(request, msg)
        return redirect('dashboard:taxes')
    ctx = {'site': site_settings, 'taxes_form': taxes_form}
    return TemplateResponse(request, 'dashboard/taxes/form.html', ctx)


@staff_member_required
@permission_required('site.manage_settings')
def fetch_tax_rates(request):
    try:
        call_command('get_vat_rates')
        msg = pgettext_lazy(
            'Dashboard message', 'Tax rates updated successfully')
        messages.success(request, msg)
    except ImproperlyConfigured:
        msg = pgettext_lazy(
            'Dashboard message',
            'Could not fetch tax rates. You have not supplied a valid API '
            'Access Key')
        messages.warning(request, msg)
    return redirect('dashboard:taxes')
