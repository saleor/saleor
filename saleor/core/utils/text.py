import bleach
from html5lib.serializer import HTMLSerializer


def trim_text(text: str, max_length: int, suffix: str=''):
    """Trims a given text in accordance to parameters.
    If text length is greater than allowed, it trims it and add a given suffix to the text.
    Note that the text + suffix is equal to the max length.

    Example:
        max length = 16
        prefix = '[...]' (5 chars)
        text = 'Hello World, everyone!' (22 chars)

        => text = 'Hello World[...]'

    :param text:
    :type text: str
    :param max_length:
    :type max_length: int
    :param suffix:
    :type suffix: str

    :rtype: str
    """
    if len(text) > max_length:
        new_length = max_length - len(suffix)
        text = '%s%s' % (text[:new_length], suffix)
    return text


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
            raise ValueError('Parameter %s is not a valid option for HTMLSerializer' % k)
        setattr(cleaner.serializer, k, v)
    return cleaner


def strip_html(text: str, **serializer_kwargs: bool):
    """Removes (strips) HTML tags from text.
    Can also take additional parameters to be passed to the serializer (see `get_cleaner`).

    :param text:
     :type text: str
    :param serializer_kwargs:
     :type serializer_kwargs: Dict[str, bool]
    :rtype: str
    """
    cleaner = get_cleaner(**serializer_kwargs)
    text = cleaner.clean(text)
    return text
