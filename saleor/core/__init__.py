from django.conf import settings
from django.core.checks import register, Warning

TOKEN_PATTERN = ('(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
                 '-[0-9a-z]{12})')
NAVIGATION_CONTEXT_NAME = 'menus'


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
