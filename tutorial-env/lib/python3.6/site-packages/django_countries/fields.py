from __future__ import unicode_literals

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse  # Python 2
try:
    basestring
except NameError:
    basestring = str  # Python 3

from django import forms
from django.core import checks, exceptions
from django.contrib.admin.filters import FieldListFilter
from django.db.models.fields import CharField, BLANK_CHOICE_DASH
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.html import escape as escape_html
from django.utils.functional import lazy

from django_countries import countries, ioc_data, widgets, filters
from django_countries.conf import settings


def country_to_text(value):
    if hasattr(value, "code"):
        value = value.code
    if value is None:
        return None
    return force_text(value)


class TemporaryEscape(object):
    __slots__ = ["country", "original_escape"]

    def __init__(self, country):
        self.country = country

    def __bool__(self):
        return self.country._escape

    __nonzero__ = __bool__

    def __enter__(self):
        self.original_escape = self.country._escape
        self.country._escape = True

    def __exit__(self, type, value, traceback):
        self.country._escape = self.original_escape


@python_2_unicode_compatible
class Country(object):
    def __init__(self, code, flag_url=None, str_attr="code", custom_countries=None):
        self.flag_url = flag_url
        self._escape = False
        self._str_attr = str_attr
        if custom_countries is countries:
            custom_countries = None
        self.custom_countries = custom_countries
        # Attempt to convert the code to the alpha2 equivalent, but this
        # is not meant to be full validation so use the given code if no
        # match was found.
        self.code = self.countries.alpha2(code) or code

    def __str__(self):
        return force_text(getattr(self, self._str_attr) or "")

    def __eq__(self, other):
        return force_text(self.code or "") == force_text(other or "")

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(force_text(self))

    def __repr__(self):
        args = ["code={country.code!r}"]
        if self.flag_url is not None:
            args.append("flag_url={country.flag_url!r}")
        if self._str_attr != "code":
            args.append("str_attr={country._str_attr!r}")
        args = ", ".join(args).format(country=self)
        return "{name}({args})".format(name=self.__class__.__name__, args=args)

    def __bool__(self):
        return bool(self.code)

    __nonzero__ = __bool__  # Python 2 compatibility.

    def __len__(self):
        return len(force_text(self))

    @property
    def countries(self):
        return self.custom_countries or countries

    @property
    def escape(self):
        return TemporaryEscape(self)

    def maybe_escape(self, text):
        if not self.escape:
            return text
        return escape_html(text)

    @property
    def name(self):
        return self.maybe_escape(self.countries.name(self.code))

    @property
    def alpha3(self):
        return self.countries.alpha3(self.code)

    @property
    def numeric(self):
        return self.countries.numeric(self.code)

    @property
    def numeric_padded(self):
        return self.countries.numeric(self.code, padded=True)

    @property
    def flag(self):
        if not self.code:
            return ""
        flag_url = self.flag_url
        if flag_url is None:
            flag_url = settings.COUNTRIES_FLAG_URL
        url = flag_url.format(code_upper=self.code, code=self.code.lower())
        if not url:
            return ""
        url = urlparse.urljoin(settings.STATIC_URL, url)
        return self.maybe_escape(url)

    @property
    def flag_css(self):
        """
        Output the css classes needed to display an HTML element as a flag
        sprite.

        Requires the use of 'flags/sprite.css' or 'flags/sprite-hq.css'.
        Usage example::

            <i class="{{ ctry.flag_css }}" aria-label="{{ ctry.code }}></i>
        """
        if not self.code:
            return ""
        return "flag-sprite flag-{} flag-_{}".format(*self.code.lower())

    @property
    def unicode_flag(self):
        """
        Generate a unicode flag for the given country.

        The logic for how these are determined can be found at:

        https://en.wikipedia.org/wiki/Regional_Indicator_Symbol

        Currently, these glyphs appear to only be supported on OS X and iOS.
        """
        if not self.code:
            return ""

        # Don't really like magic numbers, but this is the code point for [A]
        # (Regional Indicator A), minus the code point for ASCII A. By adding
        # this to the uppercase characters making up the ISO 3166-1 alpha-2
        # codes we can get the flag.
        OFFSET = 127397
        points = [ord(x) + OFFSET for x in self.code.upper()]

        try:
            # Python 3 is simple: we can just chr() the unicode points.
            return chr(points[0]) + chr(points[1])
        except ValueError:
            # Python 2 requires us to be a bit more creative. We could use
            # unichr(), but that only works if the python has been compiled
            # with wide unicode support. This method should always work.
            return ("\\U%08x\\U%08x" % tuple(points)).decode("unicode-escape")

    @staticmethod
    def country_from_ioc(ioc_code, flag_url=""):
        code = ioc_data.IOC_TO_ISO.get(ioc_code, "")
        if code == "":
            return None
        return Country(code, flag_url=flag_url)

    @property
    def ioc_code(self):
        return ioc_data.ISO_TO_IOC.get(self.code, "")


class CountryDescriptor(object):
    """
    A descriptor for country fields on a model instance. Returns a Country when
    accessed so you can do things like::

        >>> from people import Person
        >>> person = Person.object.get(name='Chris')

        >>> person.country.name
        'New Zealand'

        >>> person.country.flag
        '/static/flags/nz.gif'
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            return self
        # Check in case this field was deferred.
        if self.field.name not in instance.__dict__:
            instance.refresh_from_db(fields=[self.field.name])
        value = instance.__dict__[self.field.name]
        if self.field.multiple:
            return [self.country(code) for code in value]
        return self.country(value)

    def country(self, code):
        return Country(
            code=code,
            flag_url=self.field.countries_flag_url,
            custom_countries=self.field.countries,
        )

    def __set__(self, instance, value):
        value = self.field.get_clean_value(value)
        instance.__dict__[self.field.name] = value


class LazyChoicesMixin(widgets.LazyChoicesMixin):
    def _set_choices(self, value):
        """
        Also update the widget's choices.
        """
        super(LazyChoicesMixin, self)._set_choices(value)
        self.widget.choices = value


class LazyTypedChoiceField(LazyChoicesMixin, forms.TypedChoiceField):
    """
    A form TypedChoiceField that respects choices being a lazy object.
    """

    widget = widgets.LazySelect


class LazyTypedMultipleChoiceField(LazyChoicesMixin, forms.TypedMultipleChoiceField):
    """
    A form TypedMultipleChoiceField that respects choices being a lazy object.
    """

    widget = widgets.LazySelectMultiple


class CountryField(CharField):
    """
    A country field for Django models that provides all ISO 3166-1 countries as
    choices.
    """

    descriptor_class = CountryDescriptor

    def __init__(self, *args, **kwargs):
        countries_class = kwargs.pop("countries", None)
        self.countries = countries_class() if countries_class else countries
        self.countries_flag_url = kwargs.pop("countries_flag_url", None)
        self.blank_label = kwargs.pop("blank_label", None)
        self.multiple = kwargs.pop("multiple", None)
        kwargs["choices"] = self.countries
        if self.multiple:
            kwargs["max_length"] = len(self.countries) * 3 - 1
        else:
            kwargs["max_length"] = 2
        super(CharField, self).__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super(CountryField, self).check(**kwargs)
        errors.extend(self._check_multiple())
        return errors

    def _check_multiple(self):
        if not self.multiple or not self.null:
            return []

        hint = "Remove null=True argument on the field"
        if not self.blank:
            hint += " (just add blank=True if you want to allow no selection)"
        hint += "."

        return [
            checks.Error(
                "Field specifies multiple=True, so should not be null.",
                obj=self,
                id="django_countries.E100",
                hint=hint,
            )
        ]

    def get_internal_type(self):
        return "CharField"

    def contribute_to_class(self, cls, name):
        super(CountryField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def pre_save(self, *args, **kwargs):
        "Returns field's value just before saving."
        value = super(CharField, self).pre_save(*args, **kwargs)
        return self.get_prep_value(value)

    def get_prep_value(self, value):
        "Returns field's value prepared for saving into a database."
        value = self.get_clean_value(value)
        if self.multiple:
            if value:
                value = ",".join(value)
            else:
                value = ""
        return super(CharField, self).get_prep_value(value)

    def get_clean_value(self, value):
        if value is None:
            return None
        if not self.multiple:
            return country_to_text(value)
        if isinstance(value, (basestring, Country)):
            if isinstance(value, basestring) and "," in value:
                value = value.split(",")
            else:
                value = [value]
        return list(filter(None, [country_to_text(c) for c in value]))

    def deconstruct(self):
        """
        Remove choices from deconstructed field, as this is the country list
        and not user editable.

        Not including the ``blank_label`` property, as this isn't database
        related.
        """
        name, path, args, kwargs = super(CountryField, self).deconstruct()
        kwargs.pop("choices")
        if self.multiple:  # multiple determines the length of the field
            kwargs["multiple"] = self.multiple
        if self.countries is not countries:
            # Include the countries class if it's not the default countries
            # instance.
            kwargs["countries"] = self.countries.__class__
        return name, path, args, kwargs

    def get_choices(self, include_blank=True, blank_choice=None, *args, **kwargs):
        if blank_choice is None:
            if self.blank_label is None:
                blank_choice = BLANK_CHOICE_DASH
            else:
                blank_choice = [("", self.blank_label)]
        if self.multiple:
            include_blank = False
        return super(CountryField, self).get_choices(
            include_blank=include_blank, blank_choice=blank_choice, *args, **kwargs
        )

    get_choices = lazy(get_choices, list)

    def formfield(self, **kwargs):
        kwargs.setdefault(
            "choices_form_class",
            LazyTypedMultipleChoiceField if self.multiple else LazyTypedChoiceField,
        )
        if "coerce" not in kwargs:
            kwargs["coerce"] = super(CountryField, self).to_python
        field = super(CharField, self).formfield(**kwargs)
        return field

    def to_python(self, value):
        if not self.multiple:
            return super(CountryField, self).to_python(value)
        if not value:
            return value
        if isinstance(value, basestring):
            value = value.split(",")
        output = []
        for item in value:
            output.append(super(CountryField, self).to_python(item))
        return output

    def validate(self, value, model_instance):
        """
        Use custom validation for when using a multiple countries field.
        """
        if not self.multiple:
            return super(CountryField, self).validate(value, model_instance)

        if not self.editable:
            # Skip validation for non-editable fields.
            return

        if value:
            choices = [option_key for option_key, option_value in self.choices]
            for single_value in value:
                if single_value not in choices:
                    raise exceptions.ValidationError(
                        self.error_messages["invalid_choice"],
                        code="invalid_choice",
                        params={"value": single_value},
                    )

        if not self.blank and value in self.empty_values:
            raise exceptions.ValidationError(self.error_messages["blank"], code="blank")

    def value_to_string(self, obj):
        """
        Ensure data is serialized correctly.
        """
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


FieldListFilter.register(lambda f: isinstance(f, CountryField), filters.CountryFilter)
