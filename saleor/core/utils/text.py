# coding: utf-8

import bleach
from django.template.defaultfilters import truncatechars
from html5lib.serializer import HTMLSerializer


def get_cleaner(**serializer_kwargs: bool):
    """
    :param serializer_kwargs:
     options:
        - alphabetical_attributes
        - escape_lt_in_attrs
        - escape_rcdata
        - inject_meta_charset
        - minimize_boolean_attributes
        - omit_optional_tags
        - quote_attr_values
        - quote_char
        - resolve_entities
        - sanitize
        - space_before_trailing_solidus
        - strip_whitespace
        - use_best_quote_char
        - use_trailing_solidus
    :type serializer_kwargs: Dict[str, bool]

    :rtype: bleach.Cleaner
    """
    cleaner = bleach.Cleaner([], strip=True)
    for k, v in serializer_kwargs.items():
        if k not in HTMLSerializer.options:
            raise ValueError(
                'Parameter %s is not a valid option for HTMLSerializer' % k)
        setattr(cleaner.serializer, k, v)
    return cleaner


def strip_html(text: str, **serializer_kwargs: bool):
    """Removes (strips) HTML tags from text.
    Can also take additional parameters
    to be passed to the serializer (see `get_cleaner`).

    :param text:
     :type text: str
    :param serializer_kwargs:
     :type serializer_kwargs: Dict[str, bool]
    :rtype: str
    """
    cleaner = get_cleaner(**serializer_kwargs)
    text = cleaner.clean(text)
    return text


def strip_html_and_truncate(html_text: str, max_length: int):
    """Strips HTML tags and whitespaces from text,
    then trim the description."""
    text = strip_html(html_text, strip_whitespace=True)
    text = truncatechars(text, max_length)
    return text
