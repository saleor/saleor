from __future__ import unicode_literals

from django.conf import settings
from django.utils.text import force_text
from django.utils.translation import get_language
from geoip import geolite2


def serialize_address_form(form):
    MAP = [
        ('country', 'country'),
        ('country_area', 'level1'),
        ('city', 'level2'),
        ('city_area', 'level3'),
        ('street_address_1', 'address1'),
        ('street_address_2', 'address2'),
        ('first_name', 'firstName'),
        ('last_name', 'lastName'),
        ('company_name', 'organization'),
        ('postal_code', 'postcode')]
    state = {
        'countries': [
            {'code': id, 'label': force_text(name)}
            for id, name in form['country'].field.choices],
        'lang': get_language(),
        'prefix': form.prefix}
    for form_field_name, state_field_name in MAP:
        form_field = form[form_field_name]
        state[state_field_name] = form_field.value()
        error_state_name = '%sErrors' % (state_field_name,)
        state[error_state_name] = [
            force_text(error) for error in form_field.errors]
    return state


def get_default_country(address):
    try:
        match = geolite2.lookup(address)
    except ValueError:
        pass
    else:
        if match is not None:
            if match.country:
                return match.country
    return settings.DEFAULT_COUNTRY
