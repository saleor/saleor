# coding: utf-8

import bleach
import regex as re
from django.forms import fields
from html5lib.serializer import HTMLSerializer

# This will match from a cut word to a punctuation or whitespace
LAST_WORD_SENTENCE_RE = re.compile(r'[\p{Po}\s]\w*$', re.U)


def _get_last_word_separator_pos(text: str):
    """Get the position of the first punctuation or whitespace next to the
    first full word from the end of the sentence.

    :param text:
    :type text: str

    :rtype: Union[int, None]
    """
    match = LAST_WORD_SENTENCE_RE.search(text)
    if match:
        # position of the last stop char
        return match.start()
    return None


def trim_fullword(text: str, max_length: int):
    """Trim text to a length lesser than `max_length` without cutting words
    in their middle.

    If it failed to trim the text (first word too long), the word will be cut.

    :param text: The text to trim.
    :type text: str

    :param max_length: The maximal length of the new string to return.
    :type max_length: int

    :rtype: str
    """
    new_text = text[:max_length]

    if len(text) > max_length:
        # if the last char wasn't a punctuation or whitespace,
        # try to cut in another place or if unable,
        # just return the sentence with the word cut
        if not _get_last_word_separator_pos(text[max_length]):
            end_pos = _get_last_word_separator_pos(new_text)
            new_text = new_text[:end_pos]
    return new_text


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


def generate_seo_description(html_text: str, target_field: fields.CharField):
    """Strips HTML tags and whitespaces from text,
    then trim the description."""
    text = strip_html(html_text, strip_whitespace=True)
    text = trim_fullword(text, target_field.max_length)
    return text
