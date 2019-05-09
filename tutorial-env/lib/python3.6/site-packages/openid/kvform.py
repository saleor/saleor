import logging

__all__ = ['seqToKV', 'kvToSeq', 'dictToKV', 'kvToDict']


class KVFormError(ValueError):
    pass


def seqToKV(seq, strict=False):
    """Represent a sequence of pairs of strings as newline-terminated
    key:value pairs. The pairs are generated in the order given.

    @param seq: The pairs
    @type seq: [(str, (unicode|str))]

    @return: A string representation of the sequence
    @rtype: bytes
    """

    def err(msg):
        formatted = 'seqToKV warning: %s: %r' % (msg, seq)
        if strict:
            raise KVFormError(formatted)
        else:
            logging.warning(formatted)

    lines = []
    for k, v in seq:
        if isinstance(k, bytes):
            k = k.decode('utf-8')
        elif not isinstance(k, str):
            err('Converting key to string: %r' % k)
            k = str(k)

        if '\n' in k:
            raise KVFormError(
                'Invalid input for seqToKV: key contains newline: %r' % (k, ))

        if ':' in k:
            raise KVFormError(
                'Invalid input for seqToKV: key contains colon: %r' % (k, ))

        if k.strip() != k:
            err('Key has whitespace at beginning or end: %r' % (k, ))

        if isinstance(v, bytes):
            v = v.decode('utf-8')
        elif not isinstance(v, str):
            err('Converting value to string: %r' % (v, ))
            v = str(v)

        if '\n' in v:
            raise KVFormError(
                'Invalid input for seqToKV: value contains newline: %r' %
                (v, ))

        if v.strip() != v:
            err('Value has whitespace at beginning or end: %r' % (v, ))

        lines.append(k + ':' + v + '\n')

    return ''.join(lines).encode('utf-8')


def kvToSeq(data, strict=False):
    """

    After one parse, seqToKV and kvToSeq are inverses, with no warnings::

        seq = kvToSeq(s)
        seqToKV(kvToSeq(seq)) == seq

    @return str
    """

    def err(msg):
        formatted = 'kvToSeq warning: %s: %r' % (msg, data)
        if strict:
            raise KVFormError(formatted)
        else:
            logging.warning(formatted)

    if isinstance(data, bytes):
        data = data.decode("utf-8")

    lines = data.split('\n')
    if lines[-1]:
        err('Does not end in a newline')
    else:
        del lines[-1]

    pairs = []
    line_num = 0
    for line in lines:
        line_num += 1

        # Ignore blank lines
        if not line.strip():
            continue

        pair = line.split(':', 1)
        if len(pair) == 2:
            k, v = pair
            k_s = k.strip()
            if k_s != k:
                fmt = ('In line %d, ignoring leading or trailing '
                       'whitespace in key %r')
                err(fmt % (line_num, k))

            if not k_s:
                err('In line %d, got empty key' % (line_num, ))

            v_s = v.strip()
            if v_s != v:
                fmt = ('In line %d, ignoring leading or trailing '
                       'whitespace in value %r')
                err(fmt % (line_num, v))

            pairs.append((k_s, v_s))
        else:
            err('Line %d does not contain a colon' % line_num)

    return pairs


def dictToKV(d):
    return seqToKV(sorted(d.items()))


def kvToDict(s):
    return dict(kvToSeq(s))
