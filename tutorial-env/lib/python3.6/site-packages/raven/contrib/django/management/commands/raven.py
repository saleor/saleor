"""
raven.contrib.django.management.commands.raven
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2016 by the Sentry Team, see AUTHORS for more details
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, print_function

from django.core.management.base import BaseCommand
from optparse import make_option
from raven.scripts.runner import store_json, send_test_message

import argparse
import django
import json
import sys
import time

DJANGO_18 = django.VERSION >= (1, 8, 0)


class StoreJsonAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            value = json.loads(values[0])
        except ValueError:
            print("Invalid JSON was used for option %s.  Received: %s" % (self.dest, values[0]))
            sys.exit(1)

        setattr(namespace, self.dest, value)


class Command(BaseCommand):
    help = 'Commands to interact with the Sentry client'

    if not DJANGO_18:
        option_list = BaseCommand.option_list + (
            make_option(
                '--data', action='callback', callback=store_json,
                type='string', nargs=1, dest='data'),
            make_option(
                '--tags', action='callback', callback=store_json,
                type='string', nargs=1, dest='tags'),
        )
    else:
        def add_arguments(self, parser):
            parser.add_argument(
                'command', nargs=1,
            )
            parser.add_argument(
                '--data', action=StoreJsonAction,
                nargs=1, dest='data',
            )
            parser.add_argument(
                '--tags', action=StoreJsonAction,
                nargs=1, dest='tags',
            )

    def handle(self, command=None, *args, **options):
        if command not in ('test', ['test']):
            print('Usage: manage.py raven test')
            sys.exit(1)

        from raven.contrib.django.models import client

        send_test_message(client, {
            'tags': options.get('tags'),
            'data': options.get('data'),
        })
        time.sleep(3)
