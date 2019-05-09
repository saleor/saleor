"""Functions for generating and parsing HTTP Accept: headers for
supporting server-directed content negotiation.
"""


def generateAcceptHeader(*elements):
    """Generate an accept header value

    [str or (str, float)] -> str
    """
    parts = []
    for element in elements:
        if type(element) is str:
            qs = "1.0"
            mtype = element
        else:
            mtype, q = element
            q = float(q)
            if q > 1 or q <= 0:
                raise ValueError('Invalid preference factor: %r' % q)

            qs = '%0.1f' % (q, )

        parts.append((qs, mtype))

    parts.sort()
    chunks = []
    for q, mtype in parts:
        if q == '1.0':
            chunks.append(mtype)
        else:
            chunks.append('%s; q=%s' % (mtype, q))

    return ', '.join(chunks)


def parseAcceptHeader(value):
    """Parse an accept header, ignoring any accept-extensions

    returns a list of tuples containing main MIME type, MIME subtype,
    and quality markdown.

    str -> [(str, str, float)]
    """
    chunks = [chunk.strip() for chunk in value.split(',')]
    accept = []
    for chunk in chunks:
        parts = [s.strip() for s in chunk.split(';')]

        mtype = parts.pop(0)
        if '/' not in mtype:
            # This is not a MIME type, so ignore the bad data
            continue

        main, sub = mtype.split('/', 1)

        for ext in parts:
            if '=' in ext:
                k, v = ext.split('=', 1)
                if k == 'q':
                    try:
                        q = float(v)
                        break
                    except ValueError:
                        # Ignore poorly formed q-values
                        pass
        else:
            q = 1.0

        accept.append((q, main, sub))

    accept.sort()
    accept.reverse()
    return [(main, sub, q) for (q, main, sub) in accept]


def matchTypes(accept_types, have_types):
    """Given the result of parsing an Accept: header, and the
    available MIME types, return the acceptable types with their
    quality markdowns.

    For example:

    >>> acceptable = parseAcceptHeader('text/html, text/plain; q=0.5')
    >>> matchTypes(acceptable, ['text/plain', 'text/html', 'image/jpeg'])
    [('text/html', 1.0), ('text/plain', 0.5)]


    Type signature: ([(str, str, float)], [str]) -> [(str, float)]
    """
    if not accept_types:
        # Accept all of them
        default = 1
    else:
        default = 0

    match_main = {}
    match_sub = {}
    for (main, sub, q) in accept_types:
        if main == '*':
            default = max(default, q)
            continue
        elif sub == '*':
            match_main[main] = max(match_main.get(main, 0), q)
        else:
            match_sub[(main, sub)] = max(match_sub.get((main, sub), 0), q)

    accepted_list = []
    order_maintainer = 0
    for mtype in have_types:
        main, sub = mtype.split('/')
        if (main, sub) in match_sub:
            q = match_sub[(main, sub)]
        else:
            q = match_main.get(main, default)

        if q:
            accepted_list.append((1 - q, order_maintainer, q, mtype))
            order_maintainer += 1

    accepted_list.sort()
    return [(mtype, q) for (_, _, q, mtype) in accepted_list]


def getAcceptable(accept_header, have_types):
    """Parse the accept header and return a list of available types in
    preferred order. If a type is unacceptable, it will not be in the
    resulting list.

    This is a convenience wrapper around matchTypes and
    parseAcceptHeader.

    (str, [str]) -> [str]
    """
    accepted = parseAcceptHeader(accept_header)
    preferred = matchTypes(accepted, have_types)
    return [mtype for (mtype, _) in preferred]
