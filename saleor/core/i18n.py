from django.utils.translation import pgettext_lazy
from django_countries import countries

from . import TaxRateType

ANY_COUNTRY = ''
ANY_COUNTRY_DISPLAY = pgettext_lazy('Country choice', 'Any Country')
COUNTRY_CODE_CHOICES = [(ANY_COUNTRY, ANY_COUNTRY_DISPLAY)] + list(countries)

VAT_RATE_TYPE_TRANSLATIONS = {
    TaxRateType.ACCOMODATION: pgettext_lazy(
        'VAT rate type', 'accommodation'),
    TaxRateType.ADMISSION_TO_CULTURAL_EVENTS: pgettext_lazy(
        'VAT rate type', 'admission to cultural events'),
    TaxRateType.ADMISSION_TO_ENTERAINMENT_EVENTS: pgettext_lazy(
        'VAT rate type', 'admission to entertainment events'),
    TaxRateType.ADMISSION_TO_SPORTING_EVENTS: pgettext_lazy(
        'VAT rate type', 'admission to sporting events'),
    TaxRateType.ADVERTISING: pgettext_lazy(
        'VAT rate type', 'advertising'),
    TaxRateType.AGRICULTURAL_SUPPLIES: pgettext_lazy(
        'VAT rate type', 'agricultural supplies'),
    TaxRateType.BABY_FOODSTUFFS: pgettext_lazy(
        'VAT rate type', 'baby foodstuffs'),
    TaxRateType.BIKES: pgettext_lazy('VAT rate type', 'bikes'),
    TaxRateType.BOOKS: pgettext_lazy('VAT rate type', 'books'),
    TaxRateType.CHILDRENDS_CLOTHING: pgettext_lazy(
        'VAT rate type', 'childrens clothing'),
    TaxRateType.DOMESTIC_FUEL: pgettext_lazy(
        'VAT rate type', 'domestic fuel'),
    TaxRateType.DOMESTIC_SERVICES: pgettext_lazy(
        'VAT rate type', 'domestic services'),
    TaxRateType.E_BOOKS: pgettext_lazy('VAT rate type', 'e-books'),
    TaxRateType.FOODSTUFFS: pgettext_lazy(
        'VAT rate type', 'foodstuffs'),
    TaxRateType.HOTELS: pgettext_lazy('VAT rate type', 'hotels'),
    TaxRateType.MEDICAL: pgettext_lazy('VAT rate type', 'medical'),
    TaxRateType.NEWSPAPERS: pgettext_lazy(
        'VAT rate type', 'newspapers'),
    TaxRateType.PASSENGER_TRANSPORT: pgettext_lazy(
        'VAT rate type', 'passenger transport'),
    TaxRateType.PHARMACEUTICALS: pgettext_lazy(
        'VAT rate type', 'pharmaceuticals'),
    TaxRateType.PROPERTY_RENOVATIONS: pgettext_lazy(
        'VAT rate type', 'property renovations'),
    TaxRateType.RESTAURANTS: pgettext_lazy(
        'VAT rate type', 'restaurants'),
    TaxRateType.SOCIAL_HOUSING: pgettext_lazy(
        'VAT rate type', 'social housing'),
    TaxRateType.STANDARD: pgettext_lazy('VAT rate type', 'standard'),
    TaxRateType.WATER: pgettext_lazy('VAT rate type', 'water'),
    TaxRateType.WINE: pgettext_lazy('VAT rate type', 'wine')}
