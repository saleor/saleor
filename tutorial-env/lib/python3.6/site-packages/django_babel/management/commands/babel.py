# -*- coding: utf-8 -*-
import os
from distutils.dist import Distribution
from subprocess import call

from django.core.management.base import LabelCommand, CommandError
from django.conf import settings


__all__ = ['Command']


class Command(LabelCommand):

    args = '[makemessages] [compilemessages]'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--locale', '-l', default=[], dest='locale', action='append',
            help=(
                'Creates or updates the message files for the given locale(s)'
                ' (e.g pt_BR). Can be used multiple times.'
            ),
        )
        parser.add_argument(
            '--domain', '-d', default='django', dest='domain',
            help='The domain of the message files (default: "django").',
        ),
        parser.add_argument(
            '--mapping-file', '-F', default=None, dest='mapping_file',
            help='Mapping file',
        )

    def handle_label(self, command, **options):
        if command not in ('makemessages', 'compilemessages'):
            raise CommandError(
                "You must either apply 'makemessages' or 'compilemessages'"
            )

        if command == 'makemessages':
            self.handle_makemessages(**options)
        if command == 'compilemessages':
            self.handle_compilemessages(**options)

    def handle_makemessages(self, **options):
        locale_paths = list(settings.LOCALE_PATHS)
        domain = options.pop('domain')
        locales = options.pop('locale')

        # support for mapping file specification via setup.cfg
        # TODO: Try to support all possible options.
        distribution = Distribution()
        distribution.parse_config_files(distribution.find_config_files())

        mapping_file = options.pop('mapping_file', None)
        has_extract = 'extract_messages' in distribution.command_options
        if mapping_file is None and has_extract:
            opts = distribution.command_options['extract_messages']
            try:
                mapping_file = opts['mapping_file'][1]
            except (IndexError, KeyError):
                mapping_file = None

        for path in locale_paths:
            potfile = os.path.join(path, '%s.pot' % domain)

            if not os.path.exists(path):
                os.makedirs(path)

            if not os.path.exists(potfile):
                with open(potfile, 'wb') as fobj:
                    fobj.write(b'')

            cmd = ['pybabel', 'extract', '-o', potfile]

            if mapping_file is not None:
                cmd.extend(['-F', mapping_file])

            cmd.append(os.path.dirname(os.path.relpath(path)))

            call(cmd)

            for locale in locales:
                pofile = os.path.join(
                    os.path.dirname(potfile),
                    locale,
                    'LC_MESSAGES',
                    '%s.po' % domain)

                if not os.path.isdir(os.path.dirname(pofile)):
                    os.makedirs(os.path.dirname(pofile))

                if not os.path.exists(pofile):
                    with open(pofile, 'wb') as fobj:
                        fobj.write(b'')

                cmd = ['pybabel', 'update', '-D', domain,
                       '-i', potfile,
                       '-d', os.path.relpath(path),
                       '-l', locale]
                call(cmd)

    def handle_compilemessages(self, **options):
        locale_paths = list(settings.LOCALE_PATHS)
        domain = options.pop('domain')
        locales = options.pop('locale')

        for path in locale_paths:
            for locale in locales:
                po_file = os.path.join(
                    path, locale, 'LC_MESSAGES', domain + '.po'
                )
                if os.path.exists(po_file):
                    cmd = ['pybabel', 'compile', '-D', domain,
                           '-d', path, '-l', locale]
                    call(cmd)
