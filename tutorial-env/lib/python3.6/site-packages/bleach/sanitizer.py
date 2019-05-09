from __future__ import unicode_literals
from itertools import chain
import re
import string

import six
from six.moves.urllib.parse import urlparse
from xml.sax.saxutils import unescape

import html5lib
from html5lib.constants import (
    entities,
    namespaces,
    prefixes,
    tokenTypes,
)
try:
    from html5lib.constants import ReparseException
except ImportError:
    # html5lib-python 1.0 changed the name
    from html5lib.constants import _ReparseException as ReparseException
from html5lib.filters.base import Filter
from html5lib.filters import sanitizer
from html5lib.serializer import HTMLSerializer
from html5lib._tokenizer import HTMLTokenizer
from html5lib._trie import Trie

from bleach.utils import alphabetize_attributes, force_unicode


#: Map of entity name to expanded entity
ENTITIES = entities

#: Trie of html entity string -> character representation
ENTITIES_TRIE = Trie(ENTITIES)

#: List of allowed tags
ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'code',
    'em',
    'i',
    'li',
    'ol',
    'strong',
    'ul',
]


#: Map of allowed attributes by tag
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
}


#: List of allowed styles
ALLOWED_STYLES = []


#: List of allowed protocols
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


AMP_SPLIT_RE = re.compile('(&)')

#: Invisible characters--0 to and including 31 except 9 (tab), 10 (lf), and 13 (cr)
INVISIBLE_CHARACTERS = ''.join([chr(c) for c in chain(range(0, 9), range(11, 13), range(14, 32))])

#: Regexp for characters that are invisible
INVISIBLE_CHARACTERS_RE = re.compile(
    '[' + INVISIBLE_CHARACTERS + ']',
    re.UNICODE
)

#: String to replace invisible characters with. This can be a character, a
#: string, or even a function that takes a Python re matchobj
INVISIBLE_REPLACEMENT_CHAR = '?'


def convert_entity(value):
    """Convert an entity (minus the & and ; part) into what it represents

    This handles numeric, hex, and text entities.

    :arg value: the string (minus the ``&`` and ``;`` part) to convert

    :returns: unicode character or None if it's an ambiguous ampersand that
        doesn't match a character entity

    """
    if value[0] == '#':
        if value[1] in ('x', 'X'):
            return six.unichr(int(value[2:], 16))
        return six.unichr(int(value[1:], 10))

    return ENTITIES.get(value, None)


def convert_entities(text):
    """Converts all found entities in the text

    :arg text: the text to convert entities in

    :returns: unicode text with converted entities

    """
    if '&' not in text:
        return text

    new_text = []
    for part in next_possible_entity(text):
        if not part:
            continue

        if part.startswith('&'):
            entity = match_entity(part)
            if entity is not None:
                converted = convert_entity(entity)

                # If it's not an ambiguous ampersand, then replace with the
                # unicode character. Otherwise, we leave the entity in.
                if converted is not None:
                    new_text.append(converted)
                    remainder = part[len(entity) + 2:]
                    if part:
                        new_text.append(remainder)
                    continue

        new_text.append(part)

    return u''.join(new_text)


class BleachHTMLTokenizer(HTMLTokenizer):
    def consumeEntity(self, allowedChar=None, fromAttribute=False):
        # We don't want to consume and convert entities, so this overrides the
        # html5lib tokenizer's consumeEntity so that it's now a no-op.
        #
        # However, when that gets called, it's consumed an &, so we put that in
        # the stream.
        if fromAttribute:
            self.currentToken['data'][-1][1] += '&'

        else:
            self.tokenQueue.append({"type": tokenTypes['Characters'], "data": '&'})


class BleachHTMLParser(html5lib.HTMLParser):
    def _parse(self, stream, innerHTML=False, container="div", scripting=False, **kwargs):
        # Override HTMLParser so we can swap out the tokenizer for our own.
        self.innerHTMLMode = innerHTML
        self.container = container
        self.scripting = scripting
        self.tokenizer = BleachHTMLTokenizer(stream, parser=self, **kwargs)
        self.reset()

        try:
            self.mainLoop()
        except ReparseException:
            self.reset()
            self.mainLoop()


class Cleaner(object):
    """Cleaner for cleaning HTML fragments of malicious content

    This cleaner is a security-focused function whose sole purpose is to remove
    malicious content from a string such that it can be displayed as content in
    a web page.

    This cleaner is not designed to use to transform content to be used in
    non-web-page contexts.

    To use::

        from bleach.sanitizer import Cleaner

        cleaner = Cleaner()

        for text in all_the_yucky_things:
            sanitized = cleaner.clean(text)

    """

    def __init__(self, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES,
                 styles=ALLOWED_STYLES, protocols=ALLOWED_PROTOCOLS, strip=False,
                 strip_comments=True, filters=None):
        """Initializes a Cleaner

        :arg list tags: allowed list of tags; defaults to
            ``bleach.sanitizer.ALLOWED_TAGS``

        :arg dict attributes: allowed attributes; can be a callable, list or dict;
            defaults to ``bleach.sanitizer.ALLOWED_ATTRIBUTES``

        :arg list styles: allowed list of css styles; defaults to
            ``bleach.sanitizer.ALLOWED_STYLES``

        :arg list protocols: allowed list of protocols for links; defaults
            to ``bleach.sanitizer.ALLOWED_PROTOCOLS``

        :arg bool strip: whether or not to strip disallowed elements

        :arg bool strip_comments: whether or not to strip HTML comments

        :arg list filters: list of html5lib Filter classes to pass streamed content through

            .. seealso:: http://html5lib.readthedocs.io/en/latest/movingparts.html#filters

            .. Warning::

               Using filters changes the output of ``bleach.Cleaner.clean``.
               Make sure the way the filters change the output are secure.

        """
        self.tags = tags
        self.attributes = attributes
        self.styles = styles
        self.protocols = protocols
        self.strip = strip
        self.strip_comments = strip_comments
        self.filters = filters or []

        self.parser = BleachHTMLParser(namespaceHTMLElements=False)
        self.walker = html5lib.getTreeWalker('etree')
        self.serializer = BleachHTMLSerializer(
            quote_attr_values='always',
            omit_optional_tags=False,
            escape_lt_in_attrs=True,

            # We want to leave entities as they are without escaping or
            # resolving or expanding
            resolve_entities=False,

            # Bleach has its own sanitizer, so don't use the html5lib one
            sanitize=False,

            # Bleach sanitizer alphabetizes already, so don't use the html5lib one
            alphabetical_attributes=False,
        )

    def clean(self, text):
        """Cleans text and returns sanitized result as unicode

        :arg str text: text to be cleaned

        :returns: sanitized text as unicode

        :raises TypeError: if ``text`` is not a text type

        """
        if not isinstance(text, six.string_types):
            message = "argument cannot be of '{name}' type, must be of text type".format(
                name=text.__class__.__name__)
            raise TypeError(message)

        if not text:
            return u''

        text = force_unicode(text)

        dom = self.parser.parseFragment(text)
        filtered = BleachSanitizerFilter(
            source=self.walker(dom),

            # Bleach-sanitizer-specific things
            attributes=self.attributes,
            strip_disallowed_elements=self.strip,
            strip_html_comments=self.strip_comments,

            # html5lib-sanitizer things
            allowed_elements=self.tags,
            allowed_css_properties=self.styles,
            allowed_protocols=self.protocols,
            allowed_svg_properties=[],
        )

        # Apply any filters after the BleachSanitizerFilter
        for filter_class in self.filters:
            filtered = filter_class(source=filtered)

        return self.serializer.render(filtered)


def attribute_filter_factory(attributes):
    """Generates attribute filter function for the given attributes value

    The attributes value can take one of several shapes. This returns a filter
    function appropriate to the attributes value. One nice thing about this is
    that there's less if/then shenanigans in the ``allow_token`` method.

    """
    if callable(attributes):
        return attributes

    if isinstance(attributes, dict):
        def _attr_filter(tag, attr, value):
            if tag in attributes:
                attr_val = attributes[tag]
                if callable(attr_val):
                    return attr_val(tag, attr, value)

                if attr in attr_val:
                    return True

            if '*' in attributes:
                attr_val = attributes['*']
                if callable(attr_val):
                    return attr_val(tag, attr, value)

                return attr in attr_val

            return False

        return _attr_filter

    if isinstance(attributes, list):
        def _attr_filter(tag, attr, value):
            return attr in attributes

        return _attr_filter

    raise ValueError('attributes needs to be a callable, a list or a dict')


def match_entity(stream):
    """Returns first entity in stream or None if no entity exists

    Note: For Bleach purposes, entities must start with a "&" and end with
    a ";".

    :arg stream: the character stream

    :returns: ``None`` or the entity string without "&" or ";"

    """
    # Nix the & at the beginning
    if stream[0] != '&':
        raise ValueError('Stream should begin with "&"')

    stream = stream[1:]

    stream = list(stream)
    possible_entity = ''
    end_characters = '<&=;' + string.whitespace

    # Handle number entities
    if stream and stream[0] == '#':
        possible_entity = '#'
        stream.pop(0)

        if stream and stream[0] in ('x', 'X'):
            allowed = '0123456789abcdefABCDEF'
            possible_entity += stream.pop(0)
        else:
            allowed = '0123456789'

        # FIXME(willkg): Do we want to make sure these are valid number
        # entities? This doesn't do that currently.
        while stream and stream[0] not in end_characters:
            c = stream.pop(0)
            if c not in allowed:
                break
            possible_entity += c

        if possible_entity and stream and stream[0] == ';':
            return possible_entity
        return None

    # Handle character entities
    while stream and stream[0] not in end_characters:
        c = stream.pop(0)
        if not ENTITIES_TRIE.has_keys_with_prefix(possible_entity):
            break
        possible_entity += c

    if possible_entity and stream and stream[0] == ';':
        return possible_entity

    return None


def next_possible_entity(text):
    """Takes a text and generates a list of possible entities

    :arg text: the text to look at

    :returns: generator where each part (except the first) starts with an
        "&"

    """
    for i, part in enumerate(AMP_SPLIT_RE.split(text)):
        if i == 0:
            yield part
        elif i % 2 == 0:
            yield '&' + part


class BleachSanitizerFilter(sanitizer.Filter):
    """html5lib Filter that sanitizes text

    This filter can be used anywhere html5lib filters can be used.

    """
    def __init__(self, source, attributes=ALLOWED_ATTRIBUTES,
                 strip_disallowed_elements=False, strip_html_comments=True,
                 **kwargs):
        """Creates a BleachSanitizerFilter instance

        :arg Treewalker source: stream

        :arg list tags: allowed list of tags; defaults to
            ``bleach.sanitizer.ALLOWED_TAGS``

        :arg dict attributes: allowed attributes; can be a callable, list or dict;
            defaults to ``bleach.sanitizer.ALLOWED_ATTRIBUTES``

        :arg list styles: allowed list of css styles; defaults to
            ``bleach.sanitizer.ALLOWED_STYLES``

        :arg list protocols: allowed list of protocols for links; defaults
            to ``bleach.sanitizer.ALLOWED_PROTOCOLS``

        :arg bool strip_disallowed_elements: whether or not to strip disallowed
            elements

        :arg bool strip_html_comments: whether or not to strip HTML comments

        """
        self.attr_filter = attribute_filter_factory(attributes)

        self.strip_disallowed_elements = strip_disallowed_elements
        self.strip_html_comments = strip_html_comments

        return super(BleachSanitizerFilter, self).__init__(source, **kwargs)

    def __iter__(self):
        for token in Filter.__iter__(self):
            ret = self.sanitize_token(token)

            if not ret:
                continue

            if isinstance(ret, list):
                for subtoken in ret:
                    yield subtoken
            else:
                yield ret

    def sanitize_token(self, token):
        """Sanitize a token either by HTML-encoding or dropping.

        Unlike sanitizer.Filter, allowed_attributes can be a dict of {'tag':
        ['attribute', 'pairs'], 'tag': callable}.

        Here callable is a function with two arguments of attribute name and
        value. It should return true of false.

        Also gives the option to strip tags instead of encoding.

        :arg dict token: token to sanitize

        :returns: token or list of tokens

        """
        token_type = token['type']
        if token_type in ['StartTag', 'EndTag', 'EmptyTag']:
            if token['name'] in self.allowed_elements:
                return self.allow_token(token)

            elif self.strip_disallowed_elements:
                return None

            else:
                if 'data' in token:
                    # Alphabetize the attributes before calling .disallowed_token()
                    # so that the resulting string is stable
                    token['data'] = alphabetize_attributes(token['data'])
                return self.disallowed_token(token)

        elif token_type == 'Comment':
            if not self.strip_html_comments:
                return token
            else:
                return None

        elif token_type == 'Characters':
            return self.sanitize_characters(token)

        else:
            return token

    def sanitize_characters(self, token):
        """Handles Characters tokens

        Our overridden tokenizer doesn't do anything with entities. However,
        that means that the serializer will convert all ``&`` in Characters
        tokens to ``&amp;``.

        Since we don't want that, we extract entities here and convert them to
        Entity tokens so the serializer will let them be.

        :arg token: the Characters token to work on

        :returns: a list of tokens

        """
        data = token.get('data', '')

        if not data:
            return token

        data = INVISIBLE_CHARACTERS_RE.sub(INVISIBLE_REPLACEMENT_CHAR, data)
        token['data'] = data

        # If there isn't a & in the data, we can return now
        if '&' not in data:
            return token

        new_tokens = []

        # For each possible entity that starts with a "&", we try to extract an
        # actual entity and re-tokenize accordingly
        for part in next_possible_entity(data):
            if not part:
                continue

            if part.startswith('&'):
                entity = match_entity(part)
                if entity is not None:
                    new_tokens.append({'type': 'Entity', 'name': entity})
                    # Length of the entity plus 2--one for & at the beginning
                    # and and one for ; at the end
                    remainder = part[len(entity) + 2:]
                    if remainder:
                        new_tokens.append({'type': 'Characters', 'data': remainder})
                    continue

            new_tokens.append({'type': 'Characters', 'data': part})

        return new_tokens

    def sanitize_uri_value(self, value, allowed_protocols):
        """Checks a uri value to see if it's allowed

        :arg value: the uri value to sanitize
        :arg allowed_protocols: list of allowed protocols

        :returns: allowed value or None

        """
        # NOTE(willkg): This transforms the value into one that's easier to
        # match and verify, but shouldn't get returned since it's vastly
        # different than the original value.

        # Convert all character entities in the value
        new_value = convert_entities(value)

        # Nix backtick, space characters, and control characters
        new_value = re.sub(
            "[`\000-\040\177-\240\s]+",
            '',
            new_value
        )

        # Remove REPLACEMENT characters
        new_value = new_value.replace('\ufffd', '')

        # Lowercase it--this breaks the value, but makes it easier to match
        # against
        new_value = new_value.lower()

        try:
            # Drop attributes with uri values that have protocols that aren't
            # allowed
            parsed = urlparse(new_value)
        except ValueError:
            # URI is impossible to parse, therefore it's not allowed
            return None

        if parsed.scheme:
            # If urlparse found a scheme, check that
            if parsed.scheme in allowed_protocols:
                return value

        else:
            # Allow uris that are just an anchor
            if new_value.startswith('#'):
                return value

            # Handle protocols that urlparse doesn't recognize like "myprotocol"
            if ':' in new_value and new_value.split(':')[0] in allowed_protocols:
                return value

            # If there's no protocol/scheme specified, then assume it's "http"
            # and see if that's allowed
            if 'http' in allowed_protocols:
                return value

        return None

    def allow_token(self, token):
        """Handles the case where we're allowing the tag"""
        if 'data' in token:
            # Loop through all the attributes and drop the ones that are not
            # allowed, are unsafe or break other rules. Additionally, fix
            # attribute values that need fixing.
            #
            # At the end of this loop, we have the final set of attributes
            # we're keeping.
            attrs = {}
            for namespaced_name, val in token['data'].items():
                namespace, name = namespaced_name

                # Drop attributes that are not explicitly allowed
                #
                # NOTE(willkg): We pass in the attribute name--not a namespaced
                # name.
                if not self.attr_filter(token['name'], name, val):
                    continue

                # Drop attributes with uri values that use a disallowed protocol
                # Sanitize attributes with uri values
                if namespaced_name in self.attr_val_is_uri:
                    new_value = self.sanitize_uri_value(val, self.allowed_protocols)
                    if new_value is None:
                        continue
                    val = new_value

                # Drop values in svg attrs with non-local IRIs
                if namespaced_name in self.svg_attr_val_allows_ref:
                    new_val = re.sub(r'url\s*\(\s*[^#\s][^)]+?\)',
                                     ' ',
                                     unescape(val))
                    new_val = new_val.strip()
                    if not new_val:
                        continue

                    else:
                        # Replace the val with the unescaped version because
                        # it's a iri
                        val = new_val

                # Drop href and xlink:href attr for svg elements with non-local IRIs
                if (None, token['name']) in self.svg_allow_local_href:
                    if namespaced_name in [(None, 'href'), (namespaces['xlink'], 'href')]:
                        if re.search(r'^\s*[^#\s]', val):
                            continue

                # If it's a style attribute, sanitize it
                if namespaced_name == (None, u'style'):
                    val = self.sanitize_css(val)

                # At this point, we want to keep the attribute, so add it in
                attrs[namespaced_name] = val

            token['data'] = alphabetize_attributes(attrs)

        return token

    def disallowed_token(self, token):
        token_type = token["type"]
        if token_type == "EndTag":
            token["data"] = "</%s>" % token["name"]

        elif token["data"]:
            assert token_type in ("StartTag", "EmptyTag")
            attrs = []
            for (ns, name), v in token["data"].items():
                # If we end up with a namespace, but no name, switch them so we
                # have a valid name to use.
                if ns and not name:
                    ns, name = name, ns

                # Figure out namespaced name if the namespace is appropriate
                # and exists; if the ns isn't in prefixes, then drop it.
                if ns is None or ns not in prefixes:
                    namespaced_name = name
                else:
                    namespaced_name = '%s:%s' % (prefixes[ns], name)

                attrs.append(' %s="%s"' % (
                    namespaced_name,
                    # NOTE(willkg): HTMLSerializer escapes attribute values
                    # already, so if we do it here (like HTMLSerializer does),
                    # then we end up double-escaping.
                    v)
                )
            token["data"] = "<%s%s>" % (token["name"], ''.join(attrs))

        else:
            token["data"] = "<%s>" % token["name"]

        if token.get("selfClosing"):
            token["data"] = token["data"][:-1] + "/>"

        token["type"] = "Characters"

        del token["name"]
        return token

    def sanitize_css(self, style):
        """Sanitizes css in style tags"""
        # Convert entities in the style so that it can be parsed as CSS
        style = convert_entities(style)

        # Drop any url values before we do anything else
        style = re.compile('url\s*\(\s*[^\s)]+?\s*\)\s*').sub(' ', style)

        # The gauntlet of sanitization

        # Validate the css in the style tag and if it's not valid, then drop
        # the whole thing.
        parts = style.split(';')
        gauntlet = re.compile(
            r"""^([-/:,#%.'"\sa-zA-Z0-9!]|\w-\w|'[\s\w]+'\s*|"[\s\w]+"|\([\d,%\.\s]+\))*$"""
        )

        for part in parts:
            if not gauntlet.match(part):
                return ''

        if not re.match("^\s*([-\w]+\s*:[^:;]*(;\s*|$))*$", style):
            return ''

        clean = []
        for prop, value in re.findall('([-\w]+)\s*:\s*([^:;]*)', style):
            if not value:
                continue

            if prop.lower() in self.allowed_css_properties:
                clean.append(prop + ': ' + value + ';')

            elif prop.lower() in self.allowed_svg_properties:
                clean.append(prop + ': ' + value + ';')

        return ' '.join(clean)


class BleachHTMLSerializer(HTMLSerializer):
    """Wraps the HTMLSerializer and undoes & -> &amp; in attributes"""
    def escape_base_amp(self, stoken):
        """Escapes bare & in HTML attribute values"""
        # First, undo what the HTMLSerializer did
        stoken = stoken.replace('&amp;', '&')

        # Then, escape any bare &
        for part in next_possible_entity(stoken):
            if not part:
                continue

            if part.startswith('&'):
                entity = match_entity(part)
                # Only leave entities in that are not ambiguous. If they're
                # ambiguous, then we escape the ampersand.
                if entity is not None and convert_entity(entity) is not None:
                    yield '&' + entity + ';'

                    # Length of the entity plus 2--one for & at the beginning
                    # and and one for ; at the end
                    part = part[len(entity) + 2:]
                    if part:
                        yield part
                    continue

            yield part.replace('&', '&amp;')

    def serialize(self, treewalker, encoding=None):
        """Wrap HTMLSerializer.serialize and escape bare & in attributes"""
        in_tag = False
        after_equals = False

        for stoken in super(BleachHTMLSerializer, self).serialize(treewalker, encoding):
            if in_tag:
                if stoken == '>':
                    in_tag = False

                elif after_equals:
                    if stoken != '"':
                        for part in self.escape_base_amp(stoken):
                            yield part

                        after_equals = False
                        continue

                elif stoken == '=':
                    after_equals = True

                yield stoken
            else:
                if stoken.startswith('<'):
                    in_tag = True
                yield stoken
