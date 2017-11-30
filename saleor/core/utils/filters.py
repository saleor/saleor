from __future__ import unicode_literals

from django_countries import countries
from django.db.models import Q


def get_sort_by_choices(filter_set):
    return [(choice[0], choice[1].lower()) for choice in
            filter_set.filters['sort_by'].field.choices[1::2]]


def get_now_sorted_by(filter_set, fields, default_sort='name'):
    sort_by = filter_set.form.cleaned_data.get('sort_by')
    if sort_by:
        sort_by = fields[sort_by[0].strip('-')]
    else:
        sort_by = fields[default_sort]
    return sort_by


def filter_by_customer(queryset, name, value):
    return queryset.filter(
        Q(email__icontains=value) |
        Q(default_billing_address__first_name__icontains=value) |
        Q(default_billing_address__last_name__icontains=value))


def filter_by_order_customer(queryset, name, value):
    return queryset.filter(
        Q(user__email__icontains=value) |
        Q(user__default_billing_address__first_name__icontains=value) |
        Q(user__default_billing_address__last_name__icontains=value))


def filter_by_location(queryset, name, value):
    q = Q(default_billing_address__city__icontains=value)
    q |= Q(default_billing_address__country__icontains=value)
    country_codes = get_mapped_country_codes_from_search(value)
    for code in country_codes:
        q |= Q(default_billing_address__country__icontains=code)
    return queryset.filter(q)


def get_mapped_country_codes_from_search(value):
    country_codes = []
    for code, country in dict(countries).items():
        if value.lower() in country.lower():
            country_codes.append(code)
    return country_codes


def filter_by_date_range(queryset, name, value):
    q = Q()
    if value.start:
        q = Q(start_date__gte=value.start)
    if value.stop:
        if value.start:
            q |= Q(end_date__lte=value.stop)
        else:
            q = Q(end_date__lte=value.stop)
    return queryset.filter(q)
