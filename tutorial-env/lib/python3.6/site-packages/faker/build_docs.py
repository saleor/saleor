# coding=utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os
import pprint
import sys

import six


DOCS_ROOT = os.path.abspath(os.path.join('..', 'docs'))


def write(fh, s):
    return fh.write(s.encode('utf-8'))


def write_provider(fh, doc, provider, formatters, excludes=None):

    if excludes is None:
        excludes = []

    write(fh, '\n')
    title = "``{0}``".format(doc.get_provider_name(provider))
    write(fh, '%s\n' % title)
    write(fh, "-" * len(title))
    write(fh, '\n\n::\n')

    for signature, example in formatters.items():
        if signature in excludes:
            continue
        try:
            # `pprint` can't format sets of heterogenous types.
            if not isinstance(example, set):
                example = pprint.pformat(example, indent=4)
            lines = six.text_type(example).expandtabs().splitlines()
        except UnicodeEncodeError:
            msg = 'error on "{0}" with value "{1}"'.format(signature, example)
            raise Exception(msg)
        write(fh, '\n')
        write(fh, "\t{fake}\n{example}\n".format(
            fake=signature,
            example='\n'.join(['\t# ' + line for line in lines]),
        ))


def write_docs(*args, **kwargs):
    from faker import Faker, documentor
    from faker.config import DEFAULT_LOCALE, AVAILABLE_LOCALES

    fake = Faker(locale=DEFAULT_LOCALE)

    from faker.providers import BaseProvider
    base_provider_formatters = [f for f in dir(BaseProvider)]

    doc = documentor.Documentor(fake)

    formatters = doc.get_formatters(with_args=True, with_defaults=True)

    for provider, fakers in formatters:
        provider_name = doc.get_provider_name(provider)
        fname = os.path.join(DOCS_ROOT, 'providers', '%s.rst' % provider_name)
        with open(fname, 'wb') as fh:
            write_provider(fh, doc, provider, fakers)

    with open(os.path.join(DOCS_ROOT, 'providers.rst'), 'wb') as fh:
        write(fh, 'Providers\n')
        write(fh, '=========\n')
        write(fh, '.. toctree::\n')
        write(fh, '   :maxdepth: 2\n\n')
        [write(fh, '   providers/%s\n' % doc.get_provider_name(provider))
         for provider, fakers in formatters]

    AVAILABLE_LOCALES = sorted(AVAILABLE_LOCALES)
    for lang in AVAILABLE_LOCALES:
        fname = os.path.join(DOCS_ROOT, 'locales', '%s.rst' % lang)
        with open(fname, 'wb') as fh:
            write(fh, '\n')
            title = 'Language {0}\n'.format(lang)
            write(fh, title)
            write(fh, '=' * len(title))
            write(fh, '\n')
            fake = Faker(locale=lang)
            d = documentor.Documentor(fake)

            for p, fs in d.get_formatters(with_args=True, with_defaults=True,
                                          locale=lang,
                                          excludes=base_provider_formatters):
                write_provider(fh, d, p, fs)

    with open(os.path.join(DOCS_ROOT, 'locales.rst'), 'wb') as fh:
        write(fh, 'Locales\n')
        write(fh, '=======\n')
        write(fh, '.. toctree::\n')
        write(fh, '   :maxdepth: 2\n\n')
        [write(fh, '   locales/%s\n' % lang) for lang in AVAILABLE_LOCALES]


# wrappers for sphinx
def _main(app, *args, **kwargs):
    return write_docs(*args, **kwargs)


def setup(app):
    app.connect(str('builder-inited'), _main)


if __name__ == "__main__":
    write_docs(*sys.argv[1:])
