from __future__ import unicode_literals

from django.template import Library

register = Library()


@register.filter
def obfuscate_email(string):
    '''
    This filter obfuscates string (or object's __str__() result) with e-mail,
    returning only its first character followed by @example.com hostname.

    We are using naive e-mail validation here, just checking for @'s presence
    in filtered string, and fallback to obfuscate_string() if its not found.
    '''
    if '@' not in str(string):
        return obfuscate_string(string)
    username = str(string).split('@')[0]
    return '%s...@example.com' % str(username)[:3]


@register.filter
def obfuscate_phone(value):
    '''
    This filter obfuscates the phonenumber_field.PhoneNumber for printing.

    We fallback to obfuscate_string if value is not valid PhoneNumber or
    comaptibile object.
    '''
    try:
        if value.country_code and value.national_number:
            return '+%s...' % value.country_code
    except AttributeError:
        return obfuscate_string(value)


@register.filter
def obfuscate_string(string):
    '''
    This filter obfuscates string (or object's __str__() result), returning
    only its first character followed by ellipsis.
    '''
    if not string:
        return ''
    return '%s...' % str(string)[:3]
