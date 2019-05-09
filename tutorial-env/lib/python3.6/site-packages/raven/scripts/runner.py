"""
raven.scripts.runner
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
from __future__ import print_function

import logging
import os
import sys
import time

from optparse import OptionParser

from raven import Client, get_version
from raven.utils.json import json


def store_json(option, opt_str, value, parser):
    try:
        value = json.loads(value)
    except ValueError:
        print("Invalid JSON was used for option %s.  Received: %s" % (opt_str, value))
        sys.exit(1)
    setattr(parser.values, option.dest, value)


def get_loadavg():
    if hasattr(os, 'getloadavg'):
        return os.getloadavg()
    return None


def get_uid():
    try:
        import pwd
    except ImportError:
        return None
    try:
        return pwd.getpwuid(os.geteuid())[0]
    except KeyError:  # Sometimes fails in containers
        return None


def send_test_message(client, options):
    sys.stdout.write("Client configuration:\n")
    for k in ('base_url', 'project', 'public_key', 'secret_key'):
        sys.stdout.write('  %-15s: %s\n' % (k, getattr(client.remote, k)))
    sys.stdout.write('\n')

    remote_config = client.remote
    if not remote_config.is_active():
        sys.stdout.write("Error: DSN configuration is not valid!\n")
        sys.exit(1)

    if not client.is_enabled():
        sys.stdout.write('Error: Client reports as being disabled!\n')
        sys.exit(1)

    data = options.get('data', {
        'culprit': 'raven.scripts.runner',
        'logger': 'raven.test',
        'request': {
            'method': 'GET',
            'url': 'http://example.com',
        }
    })

    sys.stdout.write('Sending a test message... ')
    sys.stdout.flush()

    ident = client.captureMessage(
        message='This is a test message generated using ``raven test``',
        data=data,
        level=logging.INFO,
        stack=True,
        tags=options.get('tags', {}),
        extra={
            'user': get_uid(),
            'loadavg': get_loadavg(),
        },
    )

    sys.stdout.write('Event ID was %r\n' % (ident,))


def main():
    root = logging.getLogger('sentry.errors')
    root.setLevel(logging.DEBUG)
    # if len(root.handlers) == 0:
    #     root.addHandler(logging.StreamHandler())

    parser = OptionParser(version=get_version())
    parser.add_option("--data", action="callback", callback=store_json,
        type="string", nargs=1, dest="data")
    parser.add_option("--tags", action="callback", callback=store_json,
        type="string", nargs=1, dest="tags")
    (opts, args) = parser.parse_args()

    dsn = ' '.join(args[1:]) or os.environ.get('SENTRY_DSN')
    if not dsn:
        print("Error: No configuration detected!")
        print("You must either pass a DSN to the command, or set the SENTRY_DSN environment variable.")
        sys.exit(1)

    print("Using DSN configuration:")
    print(" ", dsn)
    print()

    client = Client(dsn, include_paths=['raven'])

    send_test_message(client, opts.__dict__)

    # TODO(dcramer): correctly support async models
    time.sleep(3)
    if client.state.did_fail():
        sys.stdout.write('error!\n')
        sys.exit(1)

    sys.stdout.write('success!\n')
