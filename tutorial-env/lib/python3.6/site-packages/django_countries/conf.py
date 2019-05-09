import django.conf


class AppSettings(object):
    """
    A holder for app-specific default settings that allows overriding via
    the project's settings.
    """

    def __getattribute__(self, attr):
        if attr == attr.upper():
            try:
                return getattr(django.conf.settings, attr)
            except AttributeError:
                pass
        return super(AppSettings, self).__getattribute__(attr)


class Settings(AppSettings):
    COUNTRIES_FLAG_URL = "flags/{code}.gif"
    """
    The URL for a flag.

    It can either be relative to the static url, or an absolute url.

    The location is parsed using Python's string formatting and is passed the
    following arguments:

        * code
        * code_upper

    For example: ``COUNTRIES_FLAG_URL = 'flags/16x10/{code_upper}.png'``
    """

    COUNTRIES_COMMON_NAMES = True
    """
    Whether to use the common names for some countries, as opposed to the
    official ISO name.

    Some examples:
        "Bolivia" instead of "Bolivia, Plurinational State of"
        "South Korea" instead of "Korea (the Republic of)"
        "Taiwan" instead of "Taiwan (Province of China)"
    """

    COUNTRIES_OVERRIDE = {}
    """
    A dictionary of names to override the defaults.

    Note that you will need to handle translation of customised country names.

    Setting a country's name to ``None`` will exclude it from the country list.
    For example::

        COUNTRIES_OVERRIDE = {
            'NZ': _('Middle Earth'),
            'AU': None
        }
    """

    COUNTRIES_ONLY = {}
    """
    Similar to COUNTRIES_OVERRIDE
    A dictionary of names to include in selection.

    Note that you will need to handle translation of customised country names.

    For example::

        COUNTRIES_ONLY = {
            'NZ': _('Middle Earth'),
            'AU': _('Desert'),
        }
    """

    COUNTRIES_FIRST = []
    """
    Countries matching the country codes provided in this list will be shown
    first in the countries list (in the order specified) before all the
    alphanumerically sorted countries.
    """

    COUNTRIES_FIRST_REPEAT = False
    """
    Countries listed in :attr:`COUNTRIES_FIRST` will be repeated again in the
    alphanumerically sorted list if set to ``True``.
    """

    COUNTRIES_FIRST_BREAK = None
    """
    Countries listed in :attr:`COUNTRIES_FIRST` will be followed by a null
    choice with this title (if set) before all the alphanumerically sorted
    countries.
    """

    COUNTRIES_FIRST_SORT = False
    """
    Countries listed in :attr:`COUNTRIES_FIRST` will be alphanumerically
    sorted based on their translated name instead of relying on their
    order in :attr:`COUNTRIES_FIRST`.
    """


settings = Settings()
