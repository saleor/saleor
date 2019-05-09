import re

from django.conf import settings


__all__ = ('load_config',)


DEFAULT_CONFIG = {
    'DEFAULT': {
        'CACHE': not settings.DEBUG,
        'BUNDLE_DIR_NAME': 'webpack_bundles/',
        'STATS_FILE': 'webpack-stats.json',
        # FIXME: Explore usage of fsnotify
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map']
    }
}

user_config = getattr(settings, 'WEBPACK_LOADER', DEFAULT_CONFIG)

user_config = dict(
    (name, dict(DEFAULT_CONFIG['DEFAULT'], **cfg))
    for name, cfg in user_config.items()
)

for entry in user_config.values():
    entry['ignores'] = [re.compile(I) for I in entry['IGNORE']]


def load_config(name):
    return user_config[name]
