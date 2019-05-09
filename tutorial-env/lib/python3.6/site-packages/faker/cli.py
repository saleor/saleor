# coding=utf-8

from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import argparse

import random
import six

from faker import Faker, documentor
from faker import VERSION
from faker.config import AVAILABLE_LOCALES, DEFAULT_LOCALE, META_PROVIDERS_MODULES

import logging


__author__ = 'joke2k'


def print_provider(doc, provider, formatters, excludes=None, output=None):
    output = output or sys.stdout
    if excludes is None:
        excludes = []

    print(file=output)
    print("### {0}".format(
          doc.get_provider_name(provider)), file=output)
    print(file=output)

    for signature, example in formatters.items():
        if signature in excludes:
            continue
        try:
            lines = six.text_type(example).expandtabs().splitlines()
        except UnicodeDecodeError:
            # The example is actually made of bytes.
            # We could coerce to bytes, but that would fail anyway when we wiil
            # try to `print` the line.
            lines = ["<bytes>"]
        except UnicodeEncodeError:
            raise Exception('error on "{0}" with value "{1}"'.format(
                            signature, example))
        margin = max(30, doc.max_name_len + 1)
        remains = 150 - margin
        separator = '#'
        for line in lines:
            for i in range(0, (len(line) // remains) + 1):
                print("\t{fake:<{margin}}{separator} {example}".format(
                    fake=signature,
                    separator=separator,
                    example=line[i * remains:(i + 1) * remains],
                    margin=margin,
                ), file=output)
                signature = separator = ' '


def print_doc(provider_or_field=None,
              args=None, lang=DEFAULT_LOCALE, output=None, seed=None,
              includes=None):
    args = args or []
    output = output or sys.stdout
    fake = Faker(locale=lang, includes=includes)
    fake.seed_instance(seed)

    from faker.providers import BaseProvider
    base_provider_formatters = [f for f in dir(BaseProvider)]

    if provider_or_field:
        if '.' in provider_or_field:
            parts = provider_or_field.split('.')
            locale = parts[-2] if parts[-2] in AVAILABLE_LOCALES else lang
            fake = Faker(locale, providers=[
                         provider_or_field], includes=includes)
            fake.seed_instance(seed)
            doc = documentor.Documentor(fake)
            doc.already_generated = base_provider_formatters
            print_provider(
                doc,
                fake.get_providers()[0],
                doc.get_provider_formatters(fake.get_providers()[0]),
                output=output)
        else:
            try:
                print(
                    fake.format(
                        provider_or_field,
                        *args),
                    end='',
                    file=output)
            except AttributeError:
                raise ValueError('No faker found for "{0}({1})"'.format(
                    provider_or_field, args))

    else:
        doc = documentor.Documentor(fake)

        formatters = doc.get_formatters(with_args=True, with_defaults=True)

        for provider, fakers in formatters:

            print_provider(doc, provider, fakers, output=output)

        for language in AVAILABLE_LOCALES:
            if language == lang:
                continue
            print(file=output)
            print('## LANGUAGE {0}'.format(language), file=output)
            fake = Faker(locale=language)
            fake.seed_instance(seed)
            d = documentor.Documentor(fake)

            for p, fs in d.get_formatters(with_args=True, with_defaults=True,
                                          locale=language,
                                          excludes=base_provider_formatters):
                print_provider(d, p, fs, output=output)


class Command(object):

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])

    def execute(self):
        """
        Given the command-line arguments, this creates a parser appropriate
        to that command, and runs it.
        """

        # retrieve default language from system environment
        default_locale = os.environ.get('LANG', 'en_US').split('.')[0]
        if default_locale not in AVAILABLE_LOCALES:
            default_locale = DEFAULT_LOCALE

        epilog = """supported locales:

  {0}

  Faker can take a locale as an optional argument, to return localized data. If
  no locale argument is specified, the factory falls back to the user's OS
  locale as long as it is supported by at least one of the providers.
     - for this user, the default locale is {1}.

  If the optional argument locale and/or user's default locale is not available
  for the specified provider, the factory falls back to faker's default locale,
  which is {2}.

examples:

  $ faker address
  968 Bahringer Garden Apt. 722
  Kristinaland, NJ 09890

  $ faker -l de_DE address
  Samira-Niemeier-Allee 56
  94812 Biedenkopf

  $ faker profile ssn,birthdate
  {{'ssn': u'628-10-1085', 'birthdate': '2008-03-29'}}

  $ faker -r=3 -s=";" name
  Willam Kertzmann;
  Josiah Maggio;
  Gayla Schmitt;

""".format(', '.join(sorted(AVAILABLE_LOCALES)),
           default_locale,
           DEFAULT_LOCALE)

        formatter_class = argparse.RawDescriptionHelpFormatter
        parser = argparse.ArgumentParser(
            prog=self.prog_name,
            description='{0} version {1}'.format(self.prog_name, VERSION),
            epilog=epilog,
            formatter_class=formatter_class)

        parser.add_argument("--version", action="version",
                            version="%(prog)s {0}".format(VERSION))

        parser.add_argument('-v',
                            '--verbose',
                            action='store_true',
                            help="show INFO logging events instead "
                            "of CRITICAL, which is the default. These logging "
                            "events provide insight into localization of "
                            "specific providers.")

        parser.add_argument('-o', metavar="output",
                            type=argparse.FileType('w'),
                            default=sys.stdout,
                            help="redirect output to a file")

        parser.add_argument('-l', '--lang',
                            choices=AVAILABLE_LOCALES,
                            default=default_locale,
                            metavar='LOCALE',
                            help="specify the language for a localized "
                            "provider (e.g. de_DE)")
        parser.add_argument('-r', '--repeat',
                            default=1,
                            type=int,
                            help="generate the specified number of outputs")
        parser.add_argument('-s', '--sep',
                            default='\n',
                            help="use the specified separator after each "
                            "output")

        parser.add_argument('--seed', metavar='SEED',
                            type=int,
                            help="specify a seed for the random generator so "
                            "that results are repeatable. Also compatible "
                            "with 'repeat' option")

        parser.add_argument('-i',
                            '--include',
                            default=META_PROVIDERS_MODULES,
                            nargs='*',
                            help="list of additional custom providers to "
                            "user, given as the import path of the module "
                            "containing your Provider class (not the provider "
                            "class itself)")

        parser.add_argument('fake',
                            action='store',
                            nargs='?',
                            help="name of the fake to generate output for "
                                 "(e.g. profile)")

        parser.add_argument('fake_args',
                            metavar="fake argument",
                            action='store',
                            nargs='*',
                            help="optional arguments to pass to the fake "
                                 "(e.g. the profile fake takes an optional "
                                 "list of comma separated field names as the "
                                 "first argument)")

        arguments = parser.parse_args(self.argv[1:])

        if arguments.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.CRITICAL)

        random.seed(arguments.seed)
        seeds = random.sample(range(arguments.repeat*10), arguments.repeat)

        for i in range(arguments.repeat):

            print_doc(arguments.fake,
                      arguments.fake_args,
                      lang=arguments.lang,
                      output=arguments.o,
                      seed=seeds[i],
                      includes=arguments.include,
                      )
            print(arguments.sep, file=arguments.o)

            if not arguments.fake:
                # repeat not supported for all docs
                break


def execute_from_command_line(argv=None):
    """A simple method that runs a Command."""
    if sys.stdout.encoding is None:
        print('please set python env PYTHONIOENCODING=UTF-8, example: '
              'export PYTHONIOENCODING=UTF-8, when writing to stdout',
              file=sys.stderr)
        exit(1)

    command = Command(argv)
    command.execute()
