import codecs

try:
    chr(0x10000)
except ValueError:
    # narrow python build
    UCSCHAR = [
        (0xA0, 0xD7FF),
        (0xF900, 0xFDCF),
        (0xFDF0, 0xFFEF),
    ]

    IPRIVATE = [
        (0xE000, 0xF8FF),
    ]
else:
    UCSCHAR = [
        (0xA0, 0xD7FF),
        (0xF900, 0xFDCF),
        (0xFDF0, 0xFFEF),
        (0x10000, 0x1FFFD),
        (0x20000, 0x2FFFD),
        (0x30000, 0x3FFFD),
        (0x40000, 0x4FFFD),
        (0x50000, 0x5FFFD),
        (0x60000, 0x6FFFD),
        (0x70000, 0x7FFFD),
        (0x80000, 0x8FFFD),
        (0x90000, 0x9FFFD),
        (0xA0000, 0xAFFFD),
        (0xB0000, 0xBFFFD),
        (0xC0000, 0xCFFFD),
        (0xD0000, 0xDFFFD),
        (0xE1000, 0xEFFFD),
    ]

    IPRIVATE = [
        (0xE000, 0xF8FF),
        (0xF0000, 0xFFFFD),
        (0x100000, 0x10FFFD),
    ]

_ESCAPE_RANGES = UCSCHAR + IPRIVATE


def _in_escape_range(octet):
    for start, end in _ESCAPE_RANGES:
        if start <= octet <= end:
            return True
    return False


def _starts_surrogate_pair(character):
    char_value = ord(character)
    return 0xD800 <= char_value <= 0xDBFF


def _ends_surrogate_pair(character):
    char_value = ord(character)
    return 0xDC00 <= char_value <= 0xDFFF


def _pct_encoded_replacements(chunk):
    replacements = []
    chunk_iter = iter(chunk)
    for character in chunk_iter:
        codepoint = ord(character)
        if _in_escape_range(codepoint):
            for char in chr(codepoint).encode("utf-8"):
                replacements.append("%%%X" % char)
        elif _starts_surrogate_pair(character):
            next_character = next(chunk_iter)
            for char in (character + next_character).encode("utf-8"):
                replacements.append("%%%X" % char)
        else:
            replacements.append(chr(codepoint))
    return replacements


def _pct_escape_handler(err):
    '''
    Encoding error handler that does percent-escaping of Unicode, to be used
    with codecs.register_error
    TODO: replace use of this with urllib.parse.quote as appropriate
    '''
    chunk = err.object[err.start:err.end]
    replacements = _pct_encoded_replacements(chunk)
    return ("".join(replacements), err.end)


codecs.register_error("oid_percent_escape", _pct_escape_handler)
