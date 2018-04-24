from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django_countries.fields import Country
from django_prices_vatlayer.models import VAT

from ...core.i18n import VAT_RATE_TYPE_TRANSLATIONS
from ...core.utils import get_paginator_items, get_taxes_for_country
from ...dashboard.taxes.filters import TaxFilter
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
