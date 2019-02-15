from django.conf import settings
from django.core.checks import Warning, register
from django.utils.translation import pgettext_lazy

TOKEN_PATTERN = ('(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
                 '-[0-9a-z]{12})')


@register()
def check_session_caching(app_configs, **kwargs):  # pragma: no cover
    errors = []
    cached_engines = {
        'django.contrib.sessions.backends.cache',
        'django.contrib.sessions.backends.cached_db'}
    if ('locmem' in settings.CACHES['default']['BACKEND'] and
            settings.SESSION_ENGINE in cached_engines):
        errors.append(
            Warning(
                'Session caching cannot work with locmem backend',
                'User sessions need to be globally shared, use a cache server'
                ' like Redis.',
                'saleor.W001'))
    return errors


class TaxRateType:
    ACCOMMODATION = 'accommodation'
    ADMISSION_TO_CULTURAL_EVENTS = 'admission to cultural events'
    ADMISSION_TO_ENTERTAINMENT_EVENTS = 'admission to entertainment events'
    ADMISSION_TO_SPORTING_EVENTS = 'admission to sporting events'
    ADVERTISING = 'advertising'
    AGRICULTURAL_SUPPLIES = 'agricultural supplies'
    BABY_FOODSTUFFS = 'baby foodstuffs'
    BIKES = 'bikes'
    BOOKS = 'books'
    CHILDRENDS_CLOTHING = 'childrens clothing'
    DOMESTIC_FUEL = 'domestic fuel'
    DOMESTIC_SERVICES = 'domestic services'
    E_BOOKS = 'e-books'
    FOODSTUFFS = 'foodstuffs'
    HOTELS = 'hotels'
    MEDICAL = 'medical'
    NEWSPAPERS = 'newspapers'
    PASSENGER_TRANSPORT = 'passenger transport'
    PHARMACEUTICALS = 'pharmaceuticals'
    PROPERTY_RENOVATIONS = 'property renovations'
    RESTAURANTS = 'restaurants'
    SOCIAL_HOUSING = 'social housing'
    STANDARD = 'standard'
    WATER = 'water'
    WINE = 'wine'

    CHOICES = (
        (ACCOMMODATION, pgettext_lazy('VAT rate type', 'accommodation')),
        (ADMISSION_TO_CULTURAL_EVENTS, pgettext_lazy(
            'VAT rate type', 'admission to cultural events')),
        (ADMISSION_TO_ENTERTAINMENT_EVENTS, pgettext_lazy(
            'VAT rate type', 'admission to entertainment events')),
        (ADMISSION_TO_SPORTING_EVENTS, pgettext_lazy(
            'VAT rate type', 'admission to sporting events')),
        (ADVERTISING, pgettext_lazy('VAT rate type', 'advertising')),
        (AGRICULTURAL_SUPPLIES, pgettext_lazy(
            'VAT rate type', 'agricultural supplies')),
        (BABY_FOODSTUFFS, pgettext_lazy('VAT rate type', 'baby foodstuffs')),
        (BIKES, pgettext_lazy('VAT rate type', 'bikes')),
        (BOOKS, pgettext_lazy('VAT rate type', 'books')),
        (CHILDRENDS_CLOTHING, pgettext_lazy(
            'VAT rate type', 'childrens clothing')),
        (DOMESTIC_FUEL, pgettext_lazy('VAT rate type', 'domestic fuel')),
        (DOMESTIC_SERVICES, pgettext_lazy(
            'VAT rate type', 'domestic services')),
        (E_BOOKS, pgettext_lazy('VAT rate type', 'e-books')),
        (FOODSTUFFS, pgettext_lazy('VAT rate type', 'foodstuffs')),
        (HOTELS, pgettext_lazy('VAT rate type', 'hotels')),
        (MEDICAL, pgettext_lazy('VAT rate type', 'medical')),
        (NEWSPAPERS, pgettext_lazy('VAT rate type', 'newspapers')),
        (PASSENGER_TRANSPORT, pgettext_lazy(
            'VAT rate type', 'passenger transport')),
        (PHARMACEUTICALS, pgettext_lazy(
            'VAT rate type', 'pharmaceuticals')),
        (PROPERTY_RENOVATIONS, pgettext_lazy(
            'VAT rate type', 'property renovations')),
        (RESTAURANTS, pgettext_lazy('VAT rate type', 'restaurants')),
        (SOCIAL_HOUSING, pgettext_lazy('VAT rate type', 'social housing')),
        (STANDARD, pgettext_lazy('VAT rate type', 'standard')),
        (WATER, pgettext_lazy('VAT rate type', 'water')),
        (WINE, pgettext_lazy('VAT rate type', 'wine')))
