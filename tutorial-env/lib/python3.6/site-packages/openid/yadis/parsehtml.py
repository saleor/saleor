__all__ = ['findHTMLMeta', 'MetaNotFound']

from html.parser import HTMLParser
import html.entities
import re
import sys

from openid.yadis.constants import YADIS_HEADER_NAME

# Size of the chunks to search at a time (also the amount that gets
# read at a time)
CHUNK_SIZE = 1024 * 16  # 16 KB


class ParseDone(Exception):
    """Exception to hold the URI that was located when the parse is
    finished. If the parse finishes without finding the URI, set it to
    None."""


class MetaNotFound(Exception):
    """Exception to hold the content of the page if we did not find
    the appropriate <meta> tag"""


re_flags = re.IGNORECASE | re.UNICODE | re.VERBOSE
ent_pat = r'''
&

(?: \#x (?P<hex> [a-f0-9]+ )
|   \# (?P<dec> \d+ )
|   (?P<word> \w+ )
)

;'''

ent_re = re.compile(ent_pat, re_flags)


def substituteMO(mo):
    if mo.lastgroup == 'hex':
        codepoint = int(mo.group('hex'), 16)
    elif mo.lastgroup == 'dec':
        codepoint = int(mo.group('dec'))
    else:
        assert mo.lastgroup == 'word'
        codepoint = html.entities.name2codepoint.get(mo.group('word'))

    if codepoint is None:
        return mo.group()
    else:
        return chr(codepoint)


def substituteEntities(s):
    return ent_re.sub(substituteMO, s)


class YadisHTMLParser(HTMLParser):
    """Parser that finds a meta http-equiv tag in the head of a html
    document.

    When feeding in data, if the tag is matched or it will never be
    found, the parser will raise ParseDone with the uri as the first
    attribute.

    Parsing state diagram
    =====================

    Any unlisted input does not affect the state::

                1, 2, 5                       8
               +--------------------------+  +-+
               |                          |  | |
            4  |    3       1, 2, 5, 7    v  | v
        TOP -> HTML -> HEAD ----------> TERMINATED
        | |            ^  |               ^  ^
        | | 3          |  |               |  |
        | +------------+  +-> FOUND ------+  |
        |                  6         8       |
        | 1, 2                               |
        +------------------------------------+

      1. any of </body>, </html>, </head> -> TERMINATE
      2. <body> -> TERMINATE
      3. <head> -> HEAD
      4. <html> -> HTML
      5. <html> -> TERMINATE
      6. <meta http-equiv='X-XRDS-Location'> -> FOUND
      7. <head> -> TERMINATE
      8. Any input -> TERMINATE
    """
    TOP = 0
    HTML = 1
    HEAD = 2
    FOUND = 3
    TERMINATED = 4

    def __init__(self):
        if (sys.version_info.minor <= 2):
            # Python 3.2 and below actually require the `strict` argument
            # to `html.parser.HTMLParser` -- otherwise it's deprecated and
            # we don't want to pass it
            super(YadisHTMLParser, self).__init__(strict=False)
        else:
            super(YadisHTMLParser, self).__init__()
        self.phase = self.TOP

    def _terminate(self):
        self.phase = self.TERMINATED
        raise ParseDone(None)

    def handle_endtag(self, tag):
        # If we ever see an end of head, body, or html, bail out right away.
        # [1]
        if tag in ['head', 'body', 'html']:
            self._terminate()

    def handle_starttag(self, tag, attrs):
        # if we ever see a start body tag, bail out right away, since
        # we want to prevent the meta tag from appearing in the body
        # [2]
        if tag == 'body':
            self._terminate()

        if self.phase == self.TOP:
            # At the top level, allow a html tag or a head tag to move
            # to the head or html phase
            if tag == 'head':
                # [3]
                self.phase = self.HEAD
            elif tag == 'html':
                # [4]
                self.phase = self.HTML

        elif self.phase == self.HTML:
            # if we are in the html tag, allow a head tag to move to
            # the HEAD phase. If we get another html tag, then bail
            # out
            if tag == 'head':
                # [3]
                self.phase = self.HEAD
            elif tag == 'html':
                # [5]
                self._terminate()

        elif self.phase == self.HEAD:
            # If we are in the head phase, look for the appropriate
            # meta tag. If we get a head or body tag, bail out.
            if tag == 'meta':
                attrs_d = dict(attrs)
                http_equiv = attrs_d.get('http-equiv', '').lower()
                if http_equiv == YADIS_HEADER_NAME.lower():
                    raw_attr = attrs_d.get('content')
                    yadis_loc = substituteEntities(raw_attr)
                    # [6]
                    self.phase = self.FOUND
                    raise ParseDone(yadis_loc)

            elif tag in ('head', 'html'):
                # [5], [7]
                self._terminate()

    def feed(self, chars):
        # [8]
        if self.phase in (self.TERMINATED, self.FOUND):
            self._terminate()

        return super(YadisHTMLParser, self).feed(chars)


def findHTMLMeta(stream):
    """Look for a meta http-equiv tag with the YADIS header name.

    @param stream: Source of the html text
    @type stream: Object that implements a read() method that works
        like file.read

    @return: The URI from which to fetch the XRDS document
    @rtype: str

    @raises MetaNotFound: raised with the content that was
        searched as the first parameter.
    """
    parser = YadisHTMLParser()
    chunks = []

    while 1:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            # End of file
            break

        chunks.append(chunk)
        try:
            parser.feed(chunk)
        except ParseDone as why:
            uri = why.args[0]
            if uri is None:
                # Parse finished, but we may need the rest of the file
                chunks.append(stream.read())
                break
            else:
                return uri

    content = ''.join(chunks)
    raise MetaNotFound(content)
