from django.utils.translation import pgettext_lazy
from django_countries import countries

ANY_COUNTRY = ''
ANY_COUNTRY_DISPLAY = pgettext_lazy('Country choice', 'Rest of World')
COUNTRY_CODE_CHOICES = [(ANY_COUNTRY, ANY_COUNTRY_DISPLAY)] + list(countries)

VAT_RATE_TYPE_TRANSLATIONS = {
    'accommodation': pgettext_lazy('VAT rate type', 'accommodation'),
    'admission to cultural events': pgettext_lazy(
        'VAT rate type', 'admission to cultural events'),
    'admission to entertainment events': pgettext_lazy(
        'VAT rate type', 'admission to entertainment events'),
    'admission to sporting events': pgettext_lazy(
        'VAT rate type', 'admission to sporting events'),
    'advertising': pgettext_lazy(
        'VAT rate type', 'advertising'),
    'agricultural supplies': pgettext_lazy(
        'VAT rate type', 'agricultural supplies'),
    'baby foodstuffs': pgettext_lazy('VAT rate type', 'baby foodstuffs'),
    'bikes': pgettext_lazy('VAT rate type', 'bikes'),
    'books': pgettext_lazy('VAT rate type', 'books'),
    'childrens clothing': pgettext_lazy('VAT rate type', 'childrens clothing'),
    'domestic fuel': pgettext_lazy('VAT rate type', 'domestic fuel'),
    'domestic services': pgettext_lazy('VAT rate type', 'domestic services'),
    'e-books': pgettext_lazy('VAT rate type', 'e-books'),
    'foodstuffs': pgettext_lazy('VAT rate type', 'foodstuffs'),
    'hotels': pgettext_lazy('VAT rate type', 'hotels'),
    'medical': pgettext_lazy('VAT rate type', 'medical'),
    'newspapers': pgettext_lazy('VAT rate type', 'newspapers'),
    'passenger transport': pgettext_lazy(
        'VAT rate type', 'passenger transport'),
    'pharmaceuticals': pgettext_lazy('VAT rate type', 'pharmaceuticals'),
    'property renovations': pgettext_lazy(
        'VAT rate type', 'property renovations'),
    'restaurants': pgettext_lazy('VAT rate type', 'restaurants'),
    'social housing': pgettext_lazy('VAT rate type', 'social housing'),
    'standard': pgettext_lazy('VAT rate type', 'standard'),
    'water': pgettext_lazy('VAT rate type', 'water'),
    'wine': pgettext_lazy('VAT rate type', 'wine')}
