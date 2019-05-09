from __future__ import unicode_literals

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse  # Python 2
import copy

from django.forms import widgets
from django.utils.html import escape
from django.utils.functional import Promise
from django.utils.safestring import mark_safe

from django_countries.conf import settings

COUNTRY_CHANGE_HANDLER = (
    "var e=document.getElementById('flag_' + this.id); "
    "if (e) e.src = '%s'"
    ".replace('{code}', this.value.toLowerCase() || '__')"
    ".replace('{code_upper}', this.value.toUpperCase() || '__');"
)


class LazyChoicesMixin(object):
    @property
    def choices(self):
        """
        When it's time to get the choices, if it was a lazy then figure it out
        now and memoize the result.
        """
        if isinstance(self._choices, Promise):
            self._choices = list(self._choices)
        return self._choices

    @choices.setter
    def choices(self, value):
        self._set_choices(value)

    def _set_choices(self, value):
        self._choices = value


class LazySelectMixin(LazyChoicesMixin):
    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.attrs = self.attrs.copy()
        obj.choices = copy.copy(self._choices)
        memo[id(self)] = obj
        return obj


class LazySelect(LazySelectMixin, widgets.Select):
    """
    A form Select widget that respects choices being a lazy object.
    """


class LazySelectMultiple(LazySelectMixin, widgets.SelectMultiple):
    """
    A form SelectMultiple widget that respects choices being a lazy object.
    """


class CountrySelectWidget(LazySelect):
    def __init__(self, *args, **kwargs):
        self.layout = kwargs.pop("layout", None) or (
            '{widget}<img class="country-select-flag" id="{flag_id}" '
            'style="margin: 6px 4px 0" '
            'src="{country.flag}">'
        )
        super(CountrySelectWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        from django_countries.fields import Country

        attrs = attrs or {}
        widget_id = attrs and attrs.get("id")
        if widget_id:
            flag_id = "flag_{id}".format(id=widget_id)
            attrs["onchange"] = COUNTRY_CHANGE_HANDLER % urlparse.urljoin(
                settings.STATIC_URL, settings.COUNTRIES_FLAG_URL
            )
        else:
            flag_id = ""
        # Renderer argument only added in 1.11, keeping backwards compat.
        kwargs = {"renderer": renderer} if renderer else {}
        widget_render = super(CountrySelectWidget, self).render(
            name, value, attrs, **kwargs
        )
        if isinstance(value, Country):
            country = value
        else:
            country = Country(value or "__")
        with country.escape:
            return mark_safe(
                self.layout.format(
                    widget=widget_render, country=country, flag_id=escape(flag_id)
                )
            )
