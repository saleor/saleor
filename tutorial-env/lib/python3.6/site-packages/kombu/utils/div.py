"""Div. Utilities."""
from __future__ import absolute_import, unicode_literals, print_function

from .encoding import default_encode

import sys


def emergency_dump_state(state, open_file=open, dump=None, stderr=None):
    """Dump message state to stdout or file."""
    from pprint import pformat
    from tempfile import mktemp
    stderr = sys.stderr if stderr is None else stderr

    if dump is None:
        import pickle
        dump = pickle.dump
    persist = mktemp()
    print('EMERGENCY DUMP STATE TO FILE -> {0} <-'.format(persist),  # noqa
          file=stderr)
    fh = open_file(persist, 'w')
    try:
        try:
            dump(state, fh, protocol=0)
        except Exception as exc:
            print(  # noqa
                'Cannot pickle state: {0!r}. Fallback to pformat.'.format(exc),
                file=stderr,
            )
            fh.write(default_encode(pformat(state)))
    finally:
        fh.flush()
        fh.close()
    return persist
