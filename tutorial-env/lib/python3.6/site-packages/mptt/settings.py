from django.conf import settings

"""Default level indicator. By default is `'---'`."""
DEFAULT_LEVEL_INDICATOR = getattr(settings, 'MPTT_DEFAULT_LEVEL_INDICATOR',
                                  '---')
