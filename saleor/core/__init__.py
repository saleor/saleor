from enum import Enum
from django.conf import settings
from django.core.checks import register, Warning

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


class TaxRateType(Enum):
    ACCOMODATION = 'accomodation'
    ADMISSION_TO_CULTURAL_EVENTS = 'admission to cultural events'
    ADMISSION_TO_ENTERAINMENT_EVENTS = 'admission to entertainment events'
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
